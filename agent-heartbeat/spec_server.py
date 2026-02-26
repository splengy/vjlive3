#!/usr/bin/env python3
"""
Qwen3-4B Spec Generation Server — Runs on Julie-Winters (Orange Pi 5 Max)

Loads Qwen3-4B-Instruct on the RK3588 NPU via rkllama/rkllm.
Serves a simple /generate endpoint for the heartbeat spec pipeline.

Deploy to Julie:
    scp spec_server.py happy@192.168.1.60:/home/happy/outback/
    ssh happy@192.168.1.60
    cd /home/happy/outback
    nohup /home/happy/ai_env/bin/python3 -u spec_server.py > spec_server.log 2>&1 &

API:
    POST /generate
    Body: {"prompt": "...your spec prompt..."}
    Returns: {"response": "...generated spec..."}

    GET /health
    Returns: {"status": "ok", "model": "Qwen3-4B-Instruct", "npu": true}
"""

import os
import sys
import threading
import logging

# Use Julie's AI environment
sys.path.insert(0, '/home/happy/outback')
sys.path.insert(0, '/home/happy/ai_env/lib/python3.12/site-packages')

from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger('spec_server')

app = Flask(__name__)
npu_lock = threading.Lock()

# Model path — Qwen3-4B-Instruct on the NPU
MODEL_PATH = '/AI-ENV/models/Qwen3-4B-Instruct-2507_w8a8_g128_1.2.2_rkllm/Qwen3-4B-Instruct-2507_w8a8_g128_1.2.2_rk3588.rkllm'

# Also check the other known path
ALT_MODEL_PATH = '/home/happy/models/Qwen3-4B-Instruct-2507_w8a8_g128_1.2.2_rkllm/Qwen3-4B-Instruct-2507_w8a8_g128_1.2.2_rk3588.rkllm'

# Global model handle
model = None
model_ready = False


def init_model():
    """Load Qwen3-4B on the NPU via rkllama."""
    global model, model_ready

    # Find the model file
    model_path = MODEL_PATH if os.path.exists(MODEL_PATH) else ALT_MODEL_PATH
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {MODEL_PATH} or {ALT_MODEL_PATH}")
        return False

    logger.info(f"Loading Qwen3-4B from {model_path}")

    # Try rkllama first (the wrapper used by professor.py)
    try:
        from rkllama.api.rkllm import RKLLM
        from rkllama.api.classes import callback_type

        def _callback(result, userdata, state):
            pass

        callback = callback_type(_callback)
        model = RKLLM(model_path=model_path, model_dir="./", callback=callback, options={})
        model_ready = True
        logger.info("Qwen3-4B loaded on NPU via rkllama")
        return True
    except Exception as e:
        logger.warning(f"rkllama init failed: {e}")

    # Fallback: try raw rkllm API (like vlm_server.py uses)
    try:
        import rkllm.api as rkapi
        import ctypes

        model = rkapi.RKLLM()
        model.param = rkapi.rkllm_lib.rkllm_createDefaultParam()
        model.param.model_path = model_path.encode('utf-8')
        model.param.max_context_len = 4096
        model.param.max_new_tokens = 2048
        model.param.top_k = 1
        model.param.top_p = 0.9
        model.param.temperature = 0.7
        model.param.skip_special_token = True

        ret = rkapi.rkllm_lib.rkllm_init(
            ctypes.byref(model.handle),
            ctypes.byref(model.param),
            model.cb_func
        )
        if ret != 0:
            logger.error(f"rkllm_init failed with ret={ret}")
            return False

        model_ready = True
        logger.info("Qwen3-4B loaded on NPU via raw rkllm")
        return True
    except Exception as e:
        logger.error(f"rkllm init failed: {e}")
        return False


@app.route('/health', methods=['GET'])
def health():
    """Health check for the watchdog."""
    return jsonify({
        'status': 'ok' if model_ready else 'loading',
        'model': 'Qwen3-4B-Instruct',
        'npu': model_ready,
    })


@app.route('/generate', methods=['POST'])
def generate():
    """Generate text from a prompt. Used by heartbeat for spec generation."""
    if not model_ready:
        return jsonify({'error': 'Model not loaded yet'}), 503

    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({'error': 'No prompt provided'}), 400

    prompt = data['prompt']
    max_tokens = data.get('max_tokens', 2048)

    # Qwen3 chat template
    full_prompt = (
        "<|im_start|>system\n"
        "You are a specification writer. Write clear, technical spec documents. "
        "Follow the template exactly. Use legacy code references to fill sections. "
        "Mark gaps as [NEEDS RESEARCH]. Do not write code.\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"{prompt}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    logger.info(f"Generating spec ({len(prompt)} chars prompt)")

    with npu_lock:
        try:
            params = {
                'max_new_tokens': max_tokens,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 1,
            }
            response = model.run(full_prompt, params=params)

            if response:
                logger.info(f"Generated {len(response)} chars")
                return jsonify({'response': response})
            else:
                return jsonify({'error': 'Empty response from model'}), 500

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Qwen3-4B Spec Generation Server")
    logger.info("Loading model on NPU...")
    logger.info("=" * 50)

    if init_model():
        logger.info("Model ready. Starting server on port 5050")
        app.run(host='0.0.0.0', port=5050, debug=False)
    else:
        logger.error("Failed to load model. Exiting.")
        sys.exit(1)
