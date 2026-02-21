# Plugin Manifest Examples with Licensing Metadata

This file contains comprehensive examples of plugin manifests demonstrating the new licensing metadata fields and GPU capability requirements.

## Example 1: Free Plugin (Basic)

```json
{
  "id": "visualizer.basic",
  "name": "Basic Visualizer",
  "version": "1.0.0",
  "type": "effect",
  "author": "VJLive3 Team",
  "license": "MIT",
  "description": "A simple audio visualizer plugin",
  "tags": ["visualizer", "audio", "basic"],
  "main": "main.py",
  "shaders": ["basic.vert", "basic.frag"],
  "dependencies": {},
  "parameters": [
    {
      "name": "sensitivity",
      "type": "float",
      "min": 0.1,
      "max": 10.0,
      "default": 1.0,
      "description": "Audio sensitivity"
    }
  ],
  "licensing": {
    "license_type": "free",
    "license_version": "1.0",
    "entitlements": {
      "commercial_use": true,
      "source_access": false,
      "updates_included": true,
      "support_level": "community"
    }
  },
  "gpu_tier": "NONE",
  "category": "audio",
  "minimum_opengl_version": "3.1",
  "required_extensions": []
}
```

## Example 2: Paid Plugin (One-time Purchase)

```json
{
  "id": "visualizer.pro",
  "name": "Pro Visualizer",
  "version": "2.0.0",
  "type": "effect",
  "author": "VJLive3 Pro Team",
  "license": "Proprietary",
  "description": "Advanced visualizer with custom shaders and effects",
  "tags": ["visualizer", "pro", "advanced", "shaders"],
  "main": "main.py",
  "shaders": ["pro.vert", "pro.frag", "fx.vert", "fx.frag"],
  "dependencies": {
    "numpy": "^1.21.0",
    "pillow": "^8.3.0"
  },
  "parameters": [
    {
      "name": "shader_complexity",
      "type": "int",
      "min": 1,
      "max": 5,
      "default": 3,
      "description": "Shader complexity level"
    },
    {
      "name": "enable_ray_tracing",
      "type": "bool",
      "default": false,
      "description": "Enable ray tracing effects"
    }
  ],
  "licensing": {
    "license_type": "paid",
    "license_version": "2.0",
    "price_usd": 49.99,
    "trial_period_days": 14,
    "entitlements": {
      "commercial_use": true,
      "source_access": false,
      "updates_included": true,
      "support_level": "standard"
    }
  },
  "gpu_tier": "MEDIUM",
  "category": "visual",
  "minimum_opengl_version": "3.3",
  "required_extensions": [
    "GL_ARB_compute_shader",
    "GL_EXT_texture_filter_anisotropic"
  ]
}
```

## Example 3: Subscription Plugin

```json
{
  "id": "visualizer.premium",
  "name": "Premium Visualizer",
  "version": "1.5.0",
  "type": "effect",
  "author": "VJLive3 Premium Team",
  "license": "Proprietary",
  "description": "Premium visualizer with AI-powered effects and cloud sync",
  "tags": ["visualizer", "premium", "ai", "cloud"],
  "main": "main.py",
  "shaders": ["premium.vert", "premium.frag", "ai.vert", "ai.frag"],
  "dependencies": {
    "tensorflow": "^2.5.0",
    "requests": "^2.26.0"
  },
  "parameters": [
    {
      "name": "ai_intensity",
      "type": "float",
      "min": 0.0,
      "max": 1.0,
      "default": 0.5,
      "description": "AI effect intensity"
    },
    {
      "name": "cloud_sync",
      "type": "bool",
      "default": true,
      "description": "Enable cloud synchronization"
    }
  ],
  "licensing": {
    "license_type": "subscription",
    "license_version": "1.5",
    "subscription_monthly_usd": 14.99,
    "trial_period_days": 30,
    "entitlements": {
      "commercial_use": true,
      "source_access": false,
      "updates_included": true,
      "support_level": "premium"
    }
  },
  "gpu_tier": "HIGH",
  "category": "visual",
  "minimum_opengl_version": "4.1",
  "required_extensions": [
    "GL_ARB_compute_shader",
    "GL_ARB_gpu_shader_fp64",
    "GL_NV_ray_tracing"
  ]
}
```

## Example 4: Burst Credits Plugin

```json
{
  "id": "visualizer.burst",
  "name": "Burst Visualizer",
  "version": "1.0.0",
  "type": "effect",
  "author": "VJLive3 Burst Team",
  "license": "Proprietary",
  "description": "Pay-per-use visualizer with burst credits",
  "tags": ["visualizer", "burst", "pay-per-use"],
  "main": "main.py",
  "shaders": ["burst.vert", "burst.frag"],
  "dependencies": {},
  "parameters": [
    {
      "name": "burst_mode",
      "type": "enum",
      "options": ["low", "medium", "high"],
      "default": "medium",
      "description": "Burst mode intensity"
    }
  ],
  "licensing": {
    "license_type": "burst",
    "license_version": "1.0",
    "burst_credits_required": 50,
    "entitlements": {
      "commercial_use": false,
      "source_access": false,
      "updates_included": false,
      "support_level": "community"
    }
  },
  "gpu_tier": "LOW",
  "category": "visual",
  "minimum_opengl_version": "3.1",
  "required_extensions": []
}
```

## Example 5: Node-Licensed Plugin

```json
{
  "id": "visualizer.enterprise",
  "name": "Enterprise Visualizer",
  "version": "3.0.0",
  "type": "effect",
  "author": "VJLive3 Enterprise",
  "license": "Enterprise",
  "description": "Enterprise-grade visualizer with node licensing",
  "tags": ["visualizer", "enterprise", "node", "scalable"],
  "main": "main.py",
  "shaders": ["enterprise.vert", "enterprise.frag"],
  "dependencies": {
    "redis": "^3.5.0",
    "celery": "^5.1.0"
  },
  "parameters": [
    {
      "name": "node_count",
      "type": "int",
      "min": 1,
      "max": 100,
      "default": 1,
      "description": "Number of nodes to license"
    },
    {
      "name": "enable_distributed_rendering",
      "type": "bool",
      "default": false,
      "description": "Enable distributed rendering"
    }
  ],
  "licensing": {
    "license_type": "paid",
    "license_version": "3.0",
    "price_usd": 199.99,
    "node_licensing": {
      "enabled": true,
      "per_instance": true,
      "floating_licenses": 10
    },
    "entitlements": {
      "commercial_use": true,
      "source_access": true,
      "updates_included": true,
      "support_level": "premium"
    }
  },
  "gpu_tier": "ULTRA",
  "category": "enterprise",
  "minimum_opengl_version": "4.5",
  "required_extensions": [
    "GL_ARB_compute_shader",
    "GL_ARB_gpu_shader_int64",
    "GL_NV_mesh_shader",
    "GL_NV_ray_tracing"
  ]
}
```

## Example 6: Plugin with Multiple Modules

```json
{
  "id": "modular.visualizer",
  "name": "Modular Visualizer",
  "version": "1.0.0",
  "type": "effect",
  "author": "VJLive3 Modular Team",
  "license": "MIT",
  "description": "Modular visualizer with multiple components",
  "tags": ["visualizer", "modular", "components"],
  "main": "main.py",
  "shaders": ["core.vert", "core.frag"],
  "dependencies": {},
  "modules": [
    {
      "id": "core",
      "name": "Core Visualizer",
      "description": "Main visualizer component",
      "main": "core.py",
      "parameters": [
        {
          "name": "core_intensity",
          "type": "float",
          "min": 0.0,
          "max": 1.0,
          "default": 0.5,
          "description": "Core visualizer intensity"
        }
      ]
    },
    {
      "id": "effects",
      "name": "Effects Module",
      "description": "Additional visual effects",
      "main": "effects.py",
      "parameters": [
        {
          "name": "effect_intensity",
          "type": "float",
          "min": 0.0,
          "max": 1.0,
          "default": 0.3,
          "description": "Effects intensity"
        }
      ]
    },
    {
      "id": "audio",
      "name": "Audio Module",
      "description": "Audio processing component",
      "main": "audio.py",
      "parameters": [
        {
          "name": "audio_sensitivity",
          "type": "float",
          "min": 0.1,
          "max": 10.0,
          "default": 1.0,
          "description": "Audio sensitivity"
        }
      ]
    }
  ],
  "licensing": {
    "license_type": "free",
    "license_version": "1.0",
    "entitlements": {
      "commercial_use": true,
      "source_access": false,
      "updates_included": true,
      "support_level": "community"
    }
  },
  "gpu_tier": "NONE",
  "category": "modular",
  "minimum_opengl_version": "3.1",
  "required_extensions": []
}
```

## Example 7: Plugin with Complex Dependencies

```json
{
  "id": "complex.visualizer",
  "name": "Complex Visualizer",
  "version": "2.1.0",
  "type": "effect",
  "author": "VJLive3 Complex Team",
  "license": "Proprietary",
  "description": "Complex visualizer with multiple dependencies",
  "tags": ["visualizer", "complex", "dependencies", "advanced"],
  "main": "main.py",
  "shaders": ["complex.vert", "complex.frag", "post.vert", "post.frag"],
  "dependencies": {
    "numpy": "^1.21.0",
    "pillow": "^8.3.0",
    "opencv-python": "^4.5.0",
    "scipy": "^1.7.0",
    "matplotlib": "^3.4.0"
  },
  "parameters": [
    {
      "name": "processing_mode",
      "type": "enum",
      "options": ["fast", "balanced", "quality"],
      "default": "balanced",
      "description": "Processing quality mode"
    },
    {
      "name": "enable_advanced_effects",
      "type": "bool",
      "default": false,
      "description": "Enable advanced effects"
    }
  ],
  "licensing": {
    "license_type": "paid",
    "license_version": "2.1",
    "price_usd": 79.99,
    "trial_period_days": 7,
    "entitlements": {
      "commercial_use": true,
      "source_access": false,
      "updates_included": true,
      "support_level": "standard"
    }
  },
  "gpu_tier": "MEDIUM",
  "category": "visual",
  "minimum_opengl_version": "3.3",
  "required_extensions": [
    "GL_ARB_compute_shader",
    "GL_ARB_shader_storage_buffer_object",
    "GL_EXT_texture_compression_s3tc"
  ]
}
```

## Example 8: Plugin with Preview and Repository

```json
{
  "id": "visualizer.preview",
  "name": "Preview Visualizer",
  "version": "1.0.0",
  "type": "effect",
  "author": "VJLive3 Preview Team",
  "license": "MIT",
  "description": "Visualizer with preview and repository links",
  "tags": ["visualizer", "preview", "repository"],
  "main": "main.py",
  "shaders": ["preview.vert", "preview.frag"],
  "dependencies": {},
  "parameters": [
    {
      "name": "preview_mode",
      "type": "bool",
      "default": true,
      "description": "Enable preview mode"
    }
  ],
  "licensing": {
    "license_type": "free",
    "license_version": "1.0",
    "entitlements": {
      "commercial_use": true,
      "source_access": false,
      "updates_included": true,
      "support_level": "community"
    }
  },
  "gpu_tier": "NONE",
  "category": "visual",
  "minimum_opengl_version": "3.1",
  "required_extensions": [],
  "preview": "https://example.com/previews/visualizer-preview.gif",
  "repository": "https://github.com/vjlive3/visualizer-preview"
}
```

## Key Features Demonstrated

1. **Licensing Types**: All four license types (free, paid, subscription, burst)
2. **Pricing**: One-time purchase, monthly subscription, trial periods
3. **GPU Tiers**: From NONE to ULTRA with appropriate requirements
4. **Node Licensing**: Per-instance vs floating licenses
5. **Entitlements**: Commercial use, source access, support levels
6. **Dependencies**: External library requirements
7. **Multi-module Support**: Plugins with multiple components
8. **Preview/Repository**: Marketplace integration features
9. **Backward Compatibility**: All examples work with existing systems
10. **Validation**: All fields are properly validated by the new schema

These examples serve as templates for plugin developers and demonstrate the full capabilities of the enhanced plugin manifest schema.