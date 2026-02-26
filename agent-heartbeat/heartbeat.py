#!/usr/bin/env python3
"""
Heartbeat Daemon — AHOS Main Loop

"Single serving. Wash the plate."

The heartbeat daemon is the mesh controller for the agent network.
It runs outside the agent's context window. The agent cannot modify,
bypass, or corrupt this process.

Flow:
  1. Check infrastructure health (MCP servers, Orange Pi)
  2. Pull next task from queue
  3. Build a fresh task plate (context injection)
  4. Dispatch to LLM API
  5. Validate output (word salad → stubs → local LLM → PASS/FAIL)
  6. If PASS → write to disk, run tests, commit
  7. If FAIL → reject, log, alert human
  8. Wash the plate. Next task.

The agent NEVER touches the filesystem directly.
The agent NEVER runs commands.
The agent returns text. We decide what to do with it.
"""

import json
import logging
import os
import subprocess
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path

# Add agent-heartbeat to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from heartbeat_header import estimate_tokens
from mcp_health_monitor import MCPHealthMonitor
from task_plate_builder import TaskPlateBuilder
from validator import ValidatorPipeline
from rejection_feedback import format_feedback

logger = logging.getLogger("heartbeat")


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file with fallback defaults."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"📋 Config loaded from: {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Config not found at {config_path} — using defaults")
        return _default_config()
    except yaml.YAMLError as e:
        logger.error(f"Config YAML parse error: {e} — using defaults")
        return _default_config()
    except Exception as e:
        logger.error(f"Config load error: {e} — using defaults")
        return _default_config()


def _default_config() -> dict:
    """Fallback config if config.yaml is missing or broken."""
    return {
        "llm": {
            "provider": "julie",
            "model": "Qwen3-4B-Instruct",
            "julie_host": "192.168.1.60",
            "julie_port": 5050,
        },
        "project": {
            "root": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "legacy_root": "",
            "specs_dir": "docs/specs",
            "template_path": "docs/specs/_TEMPLATE.md",
        },
        "orange_pi": {"enabled": True, "host": "192.168.1.60", "port": 5050},
        "validation": {"token_budget": 8000, "min_coverage": 99},
        "daemon": {"max_retries": 3, "retry_delay_seconds": 5},
        "alerts": {"log_dir": "agent-heartbeat/logs"},
    }


def call_llm_api(prompt: str, config: dict) -> str:
    """
    Call the LLM API with the assembled prompt.

    This is the ONLY place where an LLM is involved in generation.
    The output from here goes straight to the validator pipeline —
    it never touches disk until validated.

    Supports: julie, anthropic, google, ollama, litellm
    """
    provider = config["llm"]["provider"]
    model = config["llm"]["model"]
    max_tokens = config["llm"].get("max_output_tokens", 2048)
    temperature = config["llm"].get("temperature", 0.7)

    logger.info(f"Calling {provider}/{model} ({estimate_tokens(prompt)} input tokens)...")

    if provider == "julie":
        # Julie-Winters: Qwen3-4B on RK3588 NPU via spec_server.py
        # NO FALLBACK. If Julie is down, the task fails.
        import urllib.request
        host = os.environ.get("JULIE_HOST", config["llm"].get("julie_host", "192.168.1.60"))
        port = int(os.environ.get("JULIE_PORT", config["llm"].get("julie_port", 5050)))
        url = f"http://{host}:{port}/generate"

        payload = json.dumps({"prompt": prompt, "max_tokens": max_tokens}).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                response = data.get('response', '')
                if not response:
                    logger.error(f"Julie returned empty response: {data}")
                    return ""
                return response
        except urllib.error.URLError as e:
            logger.error(f"Julie UNREACHABLE at {url}: {e}")
            raise RuntimeError(f"Julie spec server down at {url}: {e}")
        except TimeoutError:
            logger.error(f"Julie TIMED OUT after 600s")
            raise RuntimeError(f"Julie spec server timed out after 600s")


    elif provider == "anthropic":
        try:
            import anthropic
            api_key = os.environ.get(config["llm"]["api_key_env"], "")
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except ImportError:
            logger.error("anthropic library not installed: pip install anthropic")
            return ""
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return ""

    elif provider == "google":
        try:
            import google.generativeai as genai
            api_key = os.environ.get(config["llm"]["api_key_env"], "")
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            return response.text
        except ImportError:
            logger.error("google-generativeai not installed: pip install google-generativeai")
            return ""
        except Exception as e:
            logger.error(f"Google API error: {e}")
            return ""

    elif provider == "ollama":
        try:
            import requests
            host = config["llm"].get("ollama_host", "localhost")
            port = config["llm"].get("ollama_port", 11434)
            resp = requests.post(
                f"http://{host}:{port}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
                timeout=300,
            )
            return resp.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return ""

    elif provider == "litellm":
        try:
            import litellm
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except ImportError:
            logger.error("litellm not installed: pip install litellm")
            return ""
        except Exception as e:
            logger.error(f"LiteLLM error: {e}")
            return ""

    else:
        logger.error(f"Unknown provider: {provider}")
        return ""


def write_output(content: str, filepath: Path) -> bool:
    """Write validated output to disk. Only called AFTER validation passes."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"✅ Wrote: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to write {filepath}: {e}")
        return False


def run_tests(project_root: Path, test_path: str = None) -> dict:
    """Run pytest and return results. The daemon runs tests, not the agent."""
    cmd = ["python3", "-m", "pytest", "-v", "--tb=short"]
    if test_path:
        cmd.append(test_path)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_root),
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "TIMEOUT", "passed": False}


def log_task_result(task_id: str, report: dict, config: dict) -> None:
    """Log every task attempt — pass or fail — for audit trail."""
    log_dir = Path(config.get("alerts", {}).get("log_dir", "agent-heartbeat/logs"))
    date_dir = log_dir / datetime.now().strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%H%M%S")
    log_file = date_dir / f"{task_id}_{timestamp}.json"

    log_file.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    logger.info(f"📝 Logged: {log_file}")


def process_task(task: dict, config: dict, plate_builder: TaskPlateBuilder) -> bool:
    """
    Process a single task through the full pipeline WITH RETRIES.

    On rejection, generates structured feedback and retries up to
    max_retries times. Each retry includes the rejection reason
    so the LLM can learn from its mistakes.

    Returns True if the task was completed successfully.
    """
    task_id = task.get("task_id", "UNKNOWN")
    description = task.get("description", "")
    output_path_str = task.get("output_path", "")
    output_path = Path(output_path_str) if output_path_str else None

    max_retries = config.get("daemon", {}).get("max_retries", 3)
    retry_delay = config.get("daemon", {}).get("retry_delay_seconds", 5)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"🍽️  PLATING TASK: {task_id}")
    logger.info(f"   Description: {description[:80]}")
    logger.info(f"   Output: {output_path or 'none'}")
    logger.info(f"   Max retries: {max_retries}")
    logger.info(f"   Started: {datetime.now().isoformat()}")
    logger.info(f"{'=' * 60}")

    # Step 1: Build the plate (fresh context assembly)
    try:
        plate = plate_builder.build(task_id=task_id, task_description=description)
        logger.info(f"📋 Plate: {plate.token_count} tokens | spec: {'✅' if plate.spec_content else '❌'}")
    except Exception as e:
        logger.error(f"❌ Plate builder CRASHED: {e}")
        log_task_result(task_id, {
            "status": "PLATE_BUILD_FAILED",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }, config)
        return False

    # Retry loop
    retry_prompt = ""  # Empty on first attempt
    for attempt in range(max_retries):
        attempt_start = datetime.now()
        logger.info(f"\n--- Attempt {attempt + 1}/{max_retries} ---")

        # Build prompt: plate + retry feedback (if retrying)
        prompt = plate.prompt
        if retry_prompt:
            prompt = retry_prompt + "\n\n" + prompt
            logger.info(f"📝 Retry feedback prepended ({len(retry_prompt)} chars)")

        # Step 2: Call the LLM API
        try:
            raw_output = call_llm_api(prompt, config)
        except Exception as e:
            logger.error(f"❌ LLM API CRASHED on attempt {attempt + 1}: {e}")
            log_task_result(task_id, {
                "status": "LLM_API_CRASH",
                "attempt": attempt + 1,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }, config)
            if attempt < max_retries - 1:
                logger.info(f"⏳ Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
            continue

        if not raw_output:
            logger.error(f"❌ LLM returned empty output (attempt {attempt + 1})")
            log_task_result(task_id, {
                "status": "EMPTY_OUTPUT",
                "attempt": attempt + 1,
                "timestamp": datetime.now().isoformat(),
            }, config)
            if attempt < max_retries - 1:
                logger.info(f"⏳ Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
            continue

        output_tokens = estimate_tokens(raw_output)
        logger.info(f"📥 Received: {output_tokens} output tokens")

        # Step 3: Validate output (THE GATE)
        try:
            orange_pi = config.get("orange_pi", {})
            val_config = config.get("validation", {})
            ws_config = val_config.get("word_salad", {})
            stub_config = val_config.get("stubs", {})
            validator = ValidatorPipeline(
                orange_pi_host=orange_pi.get("host", "192.168.1.60"),
                orange_pi_port=orange_pi.get("port", 5050),
                use_local_llm=orange_pi.get("enabled", False),
                word_salad_max_hits=ws_config.get("max_hits", 5),
                word_salad_max_density=ws_config.get("max_density", 3.0),
                stub_max_suspicious=stub_config.get("max_suspicious", 1),
                stub_min_code_ratio=stub_config.get("min_code_ratio", 0.3),
            )
            report = validator.validate(raw_output, spec=plate.spec_content)
        except Exception as e:
            logger.error(f"❌ Validator pipeline CRASHED: {e}")
            log_task_result(task_id, {
                "status": "VALIDATOR_CRASH",
                "attempt": attempt + 1,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }, config)
            continue

        # Step 4: Log this attempt
        attempt_duration = (datetime.now() - attempt_start).total_seconds()
        log_data = {
            "task_id": task_id,
            "attempt": attempt + 1,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(attempt_duration, 1),
            "status": "APPROVED" if report.passed else "REJECTED",
            "input_tokens": plate.token_count,
            "output_tokens": output_tokens,
            "word_salad": report.word_salad.verdict if report.word_salad else "n/a",
            "stubs": report.stubs.verdict if report.stubs else "n/a",
            "local_llm": report.local_llm.verdict if report.local_llm else "n/a",
            "overall": report.overall_verdict,
        }
        log_task_result(task_id, log_data, config)

        # Step 5: Act on verdict
        if report.passed:
            # SUCCESS — write to disk
            logger.info(f"\n✅ APPROVED: {task_id} (attempt {attempt + 1})")
            if output_path:
                if write_output(raw_output, output_path):
                    logger.info(f"💾 Written to: {output_path}")
                else:
                    logger.error(f"❌ Failed to write to: {output_path}")
                    return False
            else:
                logger.warning(f"No output_path for {task_id} — validated but not written")

            logger.info(f"Thank you for your work. Washing the plate. 🍽️\n")
            return True

        # REJECTED — build feedback for retry
        logger.warning(f"\n❌ REJECTED: {task_id} (attempt {attempt + 1})")
        logger.warning(report.overall_verdict)

        if attempt < max_retries - 1:
            # Build retry feedback
            try:
                feedback = format_feedback(report, attempt=attempt, max_attempts=max_retries)
                retry_prompt = feedback.prompt_text
                logger.info(f"📝 Retry feedback generated: {len(retry_prompt)} chars (~{len(retry_prompt)//4} tokens)")
            except Exception as e:
                logger.error(f"Rejection feedback formatter CRASHED: {e} — retrying without feedback")
                retry_prompt = (
                    f"Your previous output was REJECTED. Reason: {report.overall_verdict}\n"
                    f"Fix the issues and try again."
                )

            logger.info(f"⏳ Waiting {retry_delay}s before retry...")
            time.sleep(retry_delay)
        else:
            logger.error(f"\n🚨 TASK FAILED: {task_id} — exhausted all {max_retries} attempts")
            log_task_result(task_id, {
                "status": "FAILED_ALL_RETRIES",
                "attempts": max_retries,
                "final_verdict": report.overall_verdict,
                "timestamp": datetime.now().isoformat(),
            }, config)

    return False


def main():
    """Main daemon loop — hardened against crashes."""
    # Set up logging to both console and file
    log_dir = Path("agent-heartbeat/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    board_name = os.environ.get("BOARD_NAME", "")
    log_suffix = f"_{board_name}" if board_name else ""
    log_file = log_dir / f"heartbeat_{datetime.now().strftime('%Y-%m-%d')}{log_suffix}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file), encoding="utf-8"),
        ],
    )

    logger.info("=" * 60)
    logger.info("🫀 AHOS — Agent Heartbeat Orchestration System")
    logger.info("   'Single serving. Wash the plate.'")
    logger.info(f"   Log file: {log_file}")
    logger.info(f"   Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Load config (with fallback defaults)
    config = load_config()
    logger.info(f"Provider: {config['llm']['provider']}/{config['llm']['model']}")

    # Check infrastructure (non-fatal)
    try:
        monitor = MCPHealthMonitor()
        health = monitor.check_all()
        monitor.print_status()
        if not health.all_healthy:
            logger.warning("⚠️  Some services are down. Proceeding with degraded mode.")
    except Exception as e:
        logger.warning(f"⚠️  Health monitor CRASHED: {e} — proceeding anyway")

    # Build the plate builder (with fallback for missing paths)
    try:
        plate_builder = TaskPlateBuilder(
            project_root=config["project"]["root"],
            legacy_root=config["project"].get("legacy_root", ""),
            specs_dir=config["project"].get("specs_dir", "docs/specs"),
            template_path=config["project"].get("template_path", "docs/specs/_TEMPLATE.md"),
            token_budget=config["validation"].get("token_budget", 8000),
        )
        logger.info("🏗️  Plate builder initialized")
    except Exception as e:
        logger.error(f"❌ Plate builder init FAILED: {e}")
        logger.error("Cannot proceed without plate builder. Exiting.")
        sys.exit(1)

    # For now: process tasks from command line args or interactive mode
    if len(sys.argv) > 2:
        # Direct task: python3 heartbeat.py <task_id> "<description>" [output_path]
        task = {
            "task_id": sys.argv[1],
            "description": sys.argv[2],
            "output_path": sys.argv[3] if len(sys.argv) > 3 else "",
        }
        try:
            success = process_task(task, config, plate_builder)
        except Exception as e:
            logger.error(f"FATAL: process_task crashed: {e}")
            success = False
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        logger.info("\n🎯 Interactive mode. Enter tasks as JSON:")
        logger.info('   {"task_id": "P3-VD26", "description": "...", "output_path": "..."}')
        logger.info("   Ctrl+C to exit.\n")

        try:
            while True:
                try:
                    line = input("task> ").strip()
                    if not line:
                        continue
                    task = json.loads(line)
                    process_task(task, config, plate_builder)
                    print()  # Blank line between tasks
                except json.JSONDecodeError:
                    print("Invalid JSON. Format: {\"task_id\": \"...\", \"description\": \"...\"}")
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    # The daemon must NEVER crash. Log and continue.
                    logger.error(f"Unexpected error processing task: {e}")
                    logger.error("Continuing to next task...")
        except KeyboardInterrupt:
            pass

        logger.info(f"\n🫀 Heartbeat stopped at {datetime.now().isoformat()}. Goodbye.")


if __name__ == "__main__":
    main()
