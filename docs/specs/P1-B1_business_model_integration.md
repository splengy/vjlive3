# Spec: P1-B1 — Business Model Integration Architecture

**Phase:** Phase 1 / P1-B1
**Assigned To:** Architect
**Authorized By:** Roo Code via DISPATCH.md — SPEC-P1-B1
**Date:** 2026-02-21
**Priority:** P0
**Deadline:** 2026-02-22

---

## Overview

This specification defines the complete business model integration architecture for VJLive3's Open Core with Consumption-Based Hybrid model. It extends the existing plugin system to support:

- Plugin marketplace with licensing metadata
- GPU capability detection and filtering
- Capability-aware plugin loading
- Basic marketplace UI for free plugins
- Seamless integration with existing plugin registry, loader, and validator

**Key Principle:** Full backward compatibility with existing plugin system. All new fields are optional with sensible defaults.

---

## 1. Updated Plugin Manifest Schema

### 1.1 Current Schema (Baseline)

The existing `PluginManifest` class (in [`loader.py`](src/vjlive3/plugins/loader.py:37)) parses these fields from `plugin.json`:

```python
class PluginManifest:
    name: str
    version: str
    type: str           # effect | modifier | ui | agent
    author: str
    license: str        # SPDX identifier or "Unknown"
    description: str
    tags: List[str]
    main: str
    shaders: List[str]
    dependencies: Dict[str, str]
    parameters: List[Dict]
    preview: Optional[str]
    repository: Optional[str]
```

### 1.2 Enhanced Schema with Licensing Metadata

Add a top-level `licensing` object to `plugin.json`:

```json
{
  "id": "plugin-unique-id",
  "name": "Display Plugin",
  "version": "1.2.3",
  "type": "effect",
  "author": "Developer Name",
  "license": "MIT",
  "description": "A visual effect plugin",
  "tags": ["visual", "glitch"],
  "main": "main.py",
  "shaders": [],
  "dependencies": {},
  "parameters": [],

  "licensing": {
    "license_type": "free" | "paid" | "subscription" | "burst",
    "license_version": "1.0",
    "price_usd": 29.99,
    "subscription_monthly_usd": 9.99,
    "trial_period_days": 14,
    "burst_credits_required": 100,
    "node_licensing": {
      "enabled": false,
      "per_instance": true,
      "floating_licenses": 0
    },
    "entitlements": {
      "commercial_use": true,
      "source_access": false,
      "updates_included": true,
      "support_level": "community" | "standard" | "premium"
    }
  },

  "gpu_tier": "NONE" | "LOW" | "MEDIUM" | "HIGH" | "ULTRA",
  "category": "core" | "custom" | "experimental" | "depth" | "audio" | "modulator" | "generator",
  "minimum_opengl_version": "3.3",
  "required_extensions": ["GL_ARB_compute_shader", "GL_EXT_texture_filter_anisotropic"]
}
```

#### Licensing Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `licensing.license_type` | string | No (default: "free") | License model: free, paid, subscription, burst |
| `licensing.license_version` | string | No (default: "1.0") | License version string |
| `licensing.price_usd` | number | No | One-time purchase price in USD |
| `licensing.subscription_monthly_usd` | number | No | Monthly subscription price |
| `licensing.trial_period_days` | integer | No | Days of free trial (0 = no trial) |
| `licensing.burst_credits_required` | integer | No | Credits needed per activation |
| `licensing.node_licensing.enabled` | boolean | No (default: false) | Whether node-based licensing applies |
| `licensing.node_licensing.per_instance` | boolean | No (default: true) | License per node instance vs shared |
| `licensing.node_licensing.floating_licenses` | integer | No (default: 0) | Number of floating licenses (0 = unlimited) |
| `licensing.entitlements.commercial_use` | boolean | No (default: false) | Allow commercial use |
| `licensing.entitlements.source_access` | boolean | No (default: false) | Provide source code access |
| `licensing.entitlements.updates_included` | boolean | No (default: true) | Include updates for subscription |
| `licensing.entitlements.support_level` | string | No (default: "community") | Support tier: community, standard, premium |

#### GPU Capability Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gpu_tier` | string | No (default: "NONE") | Minimum GPU tier: NONE, LOW, MEDIUM, HIGH, ULTRA |
| `minimum_opengl_version` | string | No (default: "3.1") | Minimum OpenGL version (e.g., "3.3", "4.1") |
| `required_extensions` | array[string] | No (default: []) | Required OpenGL extensions |

### 1.3 Backward Compatibility Strategy

- All new fields are optional
- Missing `licensing` object defaults to `{"license_type": "free"}`
- Missing `gpu_tier` defaults to `"NONE"` (works on any GPU)
- Existing plugins without these fields continue to work unchanged
- `PluginValidator` validates new fields but doesn't reject old manifests

---

## 2. GPU Capability Detection System

### 2.1 Architecture

The GPU capability detection system leverages the existing ModernGL context manager ([`docs/gpu_context.md`](docs/gpu_context.md)) to query hardware capabilities.

#### Components

1. **GPUDetector** ([`src/vjlive3/plugins/gpu_detector.py`](src/vjlive3/plugins/gpu_detector.py))
   - Queries ModernGL context for GPU information
   - Computes capability tier based on hardware specs
   - Provides feature flags and extension list
   - Thread-safe singleton pattern

2. **CapabilityProfile** (dataclass)
   - `vendor: str` (e.g., "NVIDIA Corporation")
   - `renderer: str` (e.g., "GeForce RTX 4090")
   - `opengl_version: Tuple[int, int]` (major, minor)
   - `extensions: Set[str]`
   - `tier: GPUTier` (enum: NONE, LOW, MEDIUM, HIGH, ULTRA)
   - `memory_mb: int` (estimated VRAM)
   - `compute_shader: bool`
   - `features: Dict[str, bool]` (ray_tracing, mesh_shader, etc.)

### 2.2 Tier Classification Algorithm

```python
class GPUTier(Enum):
    NONE = "NONE"      # No GPU or software rendering
    LOW = "LOW"        # Integrated graphics, basic shaders
    MEDIUM = "MEDIUM"  # Mid-range discrete GPU (GTX 1060, RX 580)
    HIGH = "HIGH"      # High-end GPU (RTX 3070, RX 6800)
    ULTRA = "ULTRA"    # Enthusiast GPU (RTX 4090, RX 7900 XTX)

def detect_tier(profile: CapabilityProfile) -> GPUTier:
    # Base score from VRAM
    memory_score = {
        0: 0,      # Unknown
        1: 1,      # < 2GB
        2: 2,      # 2-4GB
        3: 3,      # 4-6GB
        4: 4,      # 6-8GB
        5: 5,      # 8-12GB
        6: 6,      # 12-16GB
        7: 7,      # 16-24GB
        8: 8,      # > 24GB
    }[clamp(memory_mb // 4, 0, 8)]

    # Bonus for compute shaders
    compute_bonus = 2 if profile.compute_shader else 0

    # Bonus for ray tracing
    rt_bonus = 1 if profile.features.get('ray_tracing', False) else 0

    total = memory_score + compute_bonus + rt_bonus

    if total >= 8: return GPUTier.ULTRA
    if total >= 6: return GPUTier.HIGH
    if total >= 4: return GPUTier.MEDIUM
    if total >= 2: return GPUTier.LOW
    return GPUTier.NONE
```

### 2.3 Integration with PluginLoader

The `PluginLoader` will query the GPU detector during initialization:

```python
from vjlive3.plugins.gpu_detector import get_gpu_detector

class PluginLoader:
    def __init__(self, context: PluginContext, plugin_dirs: List[str] = None):
        self.context = context
        self.gpu_detector = get_gpu_detector()
        self.gpu_profile = self.gpu_detector.detect()
        # ... rest of init
```

---

## 3. Capability-Aware Plugin Loading

### 3.1 Filtering Logic

The `PluginLoader` will filter discovered plugins based on GPU capability requirements:

```python
class PluginLoader:
    def is_plugin_compatible(self, manifest: PluginManifest) -> Tuple[bool, str]:
        """Check if plugin is compatible with current system.

        Returns:
            (compatible, reason_if_not)
        """
        # Check GPU tier
        required_tier = GPUTier.from_string(manifest.gpu_tier)
        if self.gpu_profile.tier.value < required_tier.value:
            return False, f"Requires GPU tier {required_tier.value}, detected {self.gpu_profile.tier.value}"

        # Check OpenGL version
        required_gl = parse_opengl_version(manifest.minimum_opengl_version)
        if self.gpu_profile.opengl_version < required_gl:
            return False, f"Requires OpenGL {manifest.minimum_opengl_version}, detected {self.gpu_profile.opengl_version_str}"

        # Check required extensions
        missing_exts = set(manifest.required_extensions) - self.gpu_profile.extensions
        if missing_exts:
            return False, f"Missing required extensions: {', '.join(missing_exts)}"

        return True, ""
```

### 3.2 Loading Behavior

- `discover_plugins()` returns all manifests (compatible and incompatible)
- `load_plugin()` checks compatibility before loading
- Incompatible plugins are marked with status `DISABLED` in registry
- Registry's `list_plugins()` includes compatibility info
- Marketplace UI filters by compatibility by default

### 3.3 User Override

Advanced users can force-load incompatible plugins via config flag:

```python
# In config or environment
VJLIVE3_ALLOW_INCOMPATIBLE_PLUGINS=true

# PluginLoader respects this
if not compatible and not self.context.config.get('allow_incompatible', False):
    return False
```

---

## 4. Marketplace UI Component

### 4.1 Backend API

New endpoints in the main application (likely FastAPI or similar):

```python
# GET /api/plugins/marketplace
# Returns: List[MarketplacePluginDTO]
class MarketplacePluginDTO(BaseModel):
    id: str
    name: str
    version: str
    description: str
    author: str
    tags: List[str]
    license_type: str
    price_usd: Optional[float]
    subscription_monthly_usd: Optional[float]
    gpu_tier: str
    category: str
    is_installed: bool
    is_compatible: bool
    preview_url: Optional[str]
    repository_url: Optional[str]

# GET /api/plugins/marketplace/{plugin_id}
# Returns: MarketplacePluginDetailDTO with full manifest

# POST /api/plugins/marketplace/{plugin_id}/install
# Body: {"license_key": "optional"}
# Installs free plugin or processes purchase/subscription

# GET /api/plugins/installed
# Returns: List[InstalledPluginDTO] with license status

# GET /api/plugins/capabilities
# Returns: CapabilityProfileDTO
```

### 4.2 Frontend Component

**MarketplaceView** (React/Vue/Qt depending on frontend stack):

```typescript
interface MarketplaceViewProps {
  plugins: MarketplacePluginDTO[];
  capabilities: CapabilityProfileDTO;
  onInstall: (pluginId: string) => void;
  onFilterChange: (filters: MarketplaceFilters) => void;
}

interface MarketplaceFilters {
  licenseType: ('free' | 'paid' | 'subscription' | 'burst')[];
  category: string[];
  minGpuTier: GPUTier;
  compatibleOnly: boolean;
  searchQuery: string;
}
```

**UI Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  [Search bar] [License filter ▼] [Category filter ▼]      │
│  [GPU tier: ████████░░] [✓ Show only compatible]          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ Card:       │  │ Card:       │  │ Card:       │      │
│  │ Glitch FX   │  │ Beat React  │  │ Deep Dream  │      │
│  │ ★★★★☆      │  │ ★★★★★      │  │ ★★★☆☆      │      │
│  │ Free        │  │ $9.99/mo    │  │ $29.99      │      │
│  │ GPU: MEDIUM │  │ GPU: LOW    │  │ GPU: HIGH   │      │
│  │ [Install]   │  │ [Subscribe] │  │ [Buy]       │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│  ... (grid of cards) ...                                   │
└─────────────────────────────────────────────────────────────┘
```

**Card Fields:**
- Plugin name and author
- Short description (truncated)
- License type badge (Free/Paid/Subscription)
- Price display (one-time or monthly)
- Star rating (future enhancement)
- GPU tier indicator (color-coded: green=compatible, red=incompatible)
- Category tag
- Action button: "Install" (free), "Buy" (paid), "Subscribe" (subscription), disabled if incompatible

### 4.3 Filtering and Search

- Real-time filtering as user types
- Filters combine with AND logic
- Compatibility filter excludes plugins requiring higher GPU tier than detected
- Search matches: name, description, tags, author

---

## 5. Integration Points with Existing Systems

### 5.1 PluginValidator Enhancements

**File:** [`src/vjlive3/plugins/validator.py`](src/vjlive3/plugins/validator.py:100)

Add validation for new fields:

```python
def validate_manifest(self, manifest: dict) -> bool:
    """
    Validate plugin manifest schema, permissions, and business metadata.
    Returns True if valid.
    """
    # ... existing required fields validation ...

    # Validate licensing metadata (business model integration)
    licensing = manifest.get('licensing', {})
    if licensing:
        # License type validation
        license_type = licensing.get('license_type')
        if license_type and license_type not in self.KNOWN_LICENSE_TYPES:
            logger.warning("Unknown license type: %s", license_type)
        
        # Price validation (must be non-negative number)
        price = licensing.get('price_usd')
        if price is not None:
            try:
                price_val = float(price)
                if price_val < 0:
                    logger.error("License price must be non-negative")
                    return False
            except (ValueError, TypeError):
                logger.error("License price must be a number")
                return False

        # Subscription price validation
        sub_price = licensing.get('subscription_monthly_usd')
        if sub_price is not None:
            try:
                sub_val = float(sub_price)
                if sub_val < 0:
                    logger.error("Subscription price must be non-negative")
                    return False
            except (ValueError, TypeError):
                logger.error("Subscription price must be a number")
                return False

        # Trial period validation
        trial_days = licensing.get('trial_period_days')
        if trial_days is not None:
            try:
                trial_val = int(trial_days)
                if trial_val < 0:
                    logger.error("Trial period must be non-negative")
                    return False
            except (ValueError, TypeError):
                logger.error("Trial period must be an integer")
                return False

        # Burst credits validation
        burst_credits = licensing.get('burst_credits_required')
        if burst_credits is not None:
            try:
                burst_val = int(burst_credits)
                if burst_val < 0:
                    logger.error("Burst credits must be non-negative")
                    return False
            except (ValueError, TypeError):
                logger.error("Burst credits must be an integer")
                return False

        # Node licensing validation
        node_lic = licensing.get('node_licensing', {})
        if node_lic:
            # Validate enabled flag
            if 'enabled' in node_lic and not isinstance(node_lic['enabled'], bool):
                logger.error("node_licensing.enabled must be a boolean")
                return False
            # Validate per_instance flag
            if 'per_instance' in node_lic and not isinstance(node_lic['per_instance'], bool):
                logger.error("node_licensing.per_instance must be a boolean")
                return False
            # Validate floating_licenses count
            float_lic = node_lic.get('floating_licenses', 0)
            try:
                int(float_lic)
            except (ValueError, TypeError):
                logger.error("node_licensing.floating_licenses must be an integer")
                return False

        # Entitlements validation
        entitlements = licensing.get('entitlements', {})
        if entitlements:
            # Validate commercial_use
            if 'commercial_use' in entitlements and not isinstance(entitlements['commercial_use'], bool):
                logger.error("entitlements.commercial_use must be a boolean")
                return False
            # Validate source_access
            if 'source_access' in entitlements and not isinstance(entitlements['source_access'], bool):
                logger.error("entitlements.source_access must be a boolean")
                return False
            # Validate updates_included
            if 'updates_included' in entitlements and not isinstance(entitlements['updates_included'], bool):
                logger.error("entitlements.updates_included must be a boolean")
                return False
            # Validate support_level
            support_level = entitlements.get('support_level')
            if support_level and support_level not in {'community', 'standard', 'premium'}:
                logger.warning("Unknown support_level: %s", support_level)

    # Validate GPU tier requirements
    gpu_tier = manifest.get('gpu_tier', 'NONE')
    if gpu_tier not in self.KNOWN_GPU_TIERS:
        logger.warning("Unknown GPU tier: %s, defaulting to NONE", gpu_tier)

    # Validate OpenGL version format
    min_gl = manifest.get('minimum_opengl_version', '3.1')
    if not re.match(r'^\d+\.\d+$', str(min_gl)):
        logger.warning("Invalid OpenGL version format: %s", min_gl)

    # Validate required extensions list
    req_ext = manifest.get('required_extensions', [])
    if not isinstance(req_ext, list):
        logger.error("required_extensions must be a list")
        return False

    # Validate category
    category = manifest.get('category', 'custom')
    if category not in self.KNOWN_CATEGORIES:
        logger.warning("Unknown category: %s", category)

    return True
```

### 5.2 PluginManifest Extension

**File:** [`src/vjlive3/plugins/loader.py`](src/vjlive3/plugins/loader.py:37)

Add new fields to `PluginManifest`:

```python
class PluginManifest:
    def __init__(self, manifest_path: Path) -> None:
        # ... existing fields ...
        self.licensing: Dict[str, Any] = data.get('licensing', {})
        self.gpu_tier: str = data.get('gpu_tier', 'NONE')
        self.minimum_opengl_version: str = data.get('minimum_opengl_version', '3.1')
        self.required_extensions: List[str] = data.get('required_extensions', [])
```

### 5.3 PluginRegistry Extension

**File:** [`src/vjlive3/plugins/registry.py`](src/vjlive3/plugins/registry.py:40)

Extend `PluginInfo` to include licensing and capability info:

```python
@dataclass
class PluginInfo:
    name: str
    class_path: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    status: PluginStatus
    error_message: Optional[str] = None
    load_time: Optional[float] = None
    instance_count: int = 0
    raw_manifest: Optional[Dict[str, Any]] = None

    # New fields for business model
    license_type: str = "free"
    price_usd: Optional[float] = None
    subscription_monthly_usd: Optional[float] = None
    gpu_tier: str = "NONE"
    is_compatible: bool = True
    compatibility_reason: Optional[str] = None
```

### 5.4 PluginLoader Capability Filtering

**File:** [`src/vjlive3/plugins/loader.py`](src/vjlive3/plugins/loader.py:99)

Add GPU detector and compatibility checking:

```python
class PluginLoader:
    def __init__(self, context: PluginContext, plugin_dirs: List[str] = None):
        self.context = context
        self.gpu_detector = get_gpu_detector()
        self.gpu_profile = self.gpu_detector.detect()
        # ... existing init ...

    def is_plugin_compatible(self, manifest: PluginManifest) -> Tuple[bool, str]:
        """Check if plugin is compatible with current GPU capabilities."""
        # GPU tier check
        required_tier = GPUTier.from_string(manifest.gpu_tier)
        if self.gpu_profile.tier.value < required_tier.value:
            return False, f"GPU tier insufficient"

        # OpenGL version check
        required_gl = parse_opengl_version(manifest.minimum_opengl_version)
        if self.gpu_profile.opengl_version < required_gl:
            return False, f"OpenGL version too old"

        # Extension check
        missing = set(manifest.required_extensions) - self.gpu_profile.extensions
        if missing:
            return False, f"Missing extensions: {', '.join(missing)}"

        return True, ""

    def load_plugin(self, manifest: PluginManifest) -> bool:
        # Check compatibility before loading
        compatible, reason = self.is_plugin_compatible(manifest)
        if not compatible and not self.context.config.get('allow_incompatible', False):
            logger.warning("[PLUGIN] Skipping %s: incompatible (%s)", manifest.name, reason)
            # Register as disabled with compatibility info
            self.registry.register_plugin(
                manifest.name,
                lambda: None,  # dummy
                {
                    'name': manifest.name,
                    'version': manifest.version,
                    'description': manifest.description,
                    'author': manifest.author,
                    'dependencies': [],
                    'status': PluginStatus.DISABLED,
                    'license_type': manifest.licensing.get('license_type', 'free'),
                    'gpu_tier': manifest.gpu_tier,
                    'is_compatible': False,
                    'compatibility_reason': reason,
                }
            )
            return False

        # ... existing load logic ...
```

### 5.5 Marketplace API Endpoints

**New file:** [`src/vjlive3/api/plugins.py`](src/vjlive3/api/plugins.py)

```python
from fastapi import APIRouter, Depends
from vjlive3.plugins.loader import get_plugin_loader
from vjlive3.plugins.gpu_detector import get_gpu_detector

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

@router.get("/marketplace")
def list_marketplace_plugins(
    loader: PluginLoader = Depends(get_plugin_loader)
) -> List[MarketplacePluginDTO]:
    """List all available plugins with marketplace metadata."""
    plugins = []
    gpu_profile = loader.gpu_profile

    for manifest in loader.available_manifests.values():
        compatible, _ = loader.is_plugin_compatible(manifest)
        dto = MarketplacePluginDTO(
            id=manifest.name,
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            tags=manifest.tags,
            license_type=manifest.licensing.get('license_type', 'free'),
            price_usd=manifest.licensing.get('price_usd'),
            subscription_monthly_usd=manifest.licensing.get('subscription_monthly_usd'),
            gpu_tier=manifest.gpu_tier,
            category=manifest.category,
            is_installed=manifest.name in loader.plugins,
            is_compatible=compatible,
            preview_url=manifest.preview,
            repository_url=manifest.repository,
        )
        plugins.append(dto)

    return plugins

@router.get("/capabilities")
def get_capabilities(
    detector: GPUDetector = Depends(get_gpu_detector)
) -> CapabilityProfileDTO:
    """Return current GPU capability profile."""
    profile = detector.detect()
    return CapabilityProfileDTO(**profile.to_dict())
```

---

## 6. Test Plan for Business Model Features

### 6.1 Unit Tests

**File:** [`tests/unit/test_plugin_system.py`](tests/unit/test_plugin_system.py) - `TestPluginValidator` class

The comprehensive test suite covers all licensing validation scenarios:

#### Licensing Validation Tests (15 tests)

- `test_license_free_valid` - Validates free license type
- `test_license_paid_valid` - Validates paid license with price
- `test_license_subscription_valid` - Validates subscription with monthly price
- `test_license_burst_valid` - Validates burst license with credits
- `test_license_negative_price_rejected` - Rejects negative price
- `test_license_negative_subscription_rejected` - Rejects negative subscription price
- `test_license_negative_trial_rejected` - Rejects negative trial period
- `test_license_negative_burst_credits_rejected` - Rejects negative burst credits
- `test_license_invalid_price_type_rejected` - Rejects non-numeric price
- `test_license_invalid_subscription_type_rejected` - Rejects non-numeric subscription
- `test_license_unknown_type_warns_but_valid` - Unknown type warns but passes (backward compat)
- `test_node_licensing_enabled_bool` - Validates node licensing with enabled=True
- `test_node_licensing_disabled_bool` - Validates node licensing with enabled=False
- `test_node_licensing_invalid_enabled_type` - Rejects non-boolean enabled
- `test_node_licensing_invalid_per_instance_type` - Rejects non-boolean per_instance
- `test_node_licensing_invalid_floating_licenses_type` - Rejects non-integer floating_licenses
- `test_entitlements_commercial_use_bool` - Validates entitlements with boolean values
- `test_entitlements_invalid_commercial_use_type` - Rejects non-boolean commercial_use
- `test_entitlements_invalid_source_access_type` - Rejects non-boolean source_access
- `test_entitlements_invalid_updates_included_type` - Rejects non-boolean updates_included
- `test_entitlements_unknown_support_level_warns` - Unknown support_level warns but passes
- `test_entitlements_valid_support_levels` - Validates all three support levels (community, standard, premium)

#### GPU Tier and Capability Validation Tests (11 tests)

- `test_gpu_tier_none_valid` - Validates NONE tier
- `test_gpu_tier_low_valid` - Validates LOW tier
- `test_gpu_tier_medium_valid` - Validates MEDIUM tier
- `test_gpu_tier_high_valid` - Validates HIGH tier
- `test_gpu_tier_ultra_valid` - Validates ULTRA tier
- `test_gpu_tier_unknown_warns` - Unknown tier warns but passes
- `test_opengl_version_valid_format` - Validates correct version format (e.g., "3.3")
- `test_opengl_version_invalid_format_warns` - Invalid format warns but passes
- `test_required_extensions_valid_list` - Validates list of extensions
- `test_required_extensions_empty_list` - Validates empty list
- `test_required_extensions_not_list_rejected` - Rejects non-list value

#### Category Validation Tests (8 tests)

- `test_category_core_valid` - Validates "core" category
- `test_category_custom_valid` - Validates "custom" category
- `test_category_experimental_valid` - Validates "experimental" category
- `test_category_depth_valid` - Validates "depth" category
- `test_category_audio_valid` - Validates "audio" category
- `test_category_modulator_valid` - Validates "modulator" category
- `test_category_generator_valid` - Validates "generator" category
- `test_category_unknown_warns` - Unknown category warns but passes

#### Backward Compatibility Tests (5 tests)

- `test_manifest_without_licensing_valid` - Old manifests without licensing field still valid
- `test_manifest_without_gpu_tier_valid` - Old manifests without gpu_tier still valid
- `test_manifest_without_category_valid` - Old manifests without category still valid
- `test_manifest_without_required_extensions_valid` - Old manifests without required_extensions still valid
- `test_manifest_without_opengl_version_valid` - Old manifests without minimum_opengl_version still valid

**Total coverage for PluginValidator:** 40+ tests covering all validation logic with proper error handling and backward compatibility.

### 6.2 Integration Tests

**Future:** [`tests/integration/test_marketplace_api.py`](tests/integration/test_marketplace_api.py)

These tests will verify the marketplace API endpoints once implemented:

- `test_marketplace_list_includes_licensing_info` - Ensures all licensing fields in response
- `test_marketplace_filters_by_license_type` - Tests license type filtering
- `test_marketplace_filters_by_compatibility` - Tests compatibility filtering
- `test_capabilities_endpoint_returns_profile` - Validates GPU capability endpoint

### 6.3 End-to-End Tests

**Future:** E2E tests for complete plugin installation workflow:

- `test_install_free_plugin_workflow` - Full flow from marketplace listing to loaded plugin

### 6.4 Performance Tests

**Future:** Performance benchmarks:

- `test_gpu_detection_performance` - Ensures GPU detection completes in < 1 second
- `test_marketplace_list_performance` - Ensures marketplace listing returns in < 200ms with 100 plugins

---

## 7. Implementation Status

### Completed (P1-B1)

- ✅ `PluginValidator` enhanced with full licensing metadata validation
- ✅ All validation rules implemented with proper error handling
- ✅ Comprehensive unit tests (40+ tests) in `test_plugin_system.py`
- ✅ Backward compatibility ensured - old manifests still work
- ✅ Plugin manifest examples created with 8 comprehensive examples
- ✅ Documentation updated with validation rules and examples

### Future Work (P1-B2 and beyond)

- ⏳ `GPUDetector` implementation (not in scope for validator task)
- ⏳ `PluginLoader` compatibility filtering
- ⏳ `PluginInfo` extension with licensing fields
- ⏳ Marketplace API endpoints
- ⏳ Integration and E2E tests

---

## 7. Data Structures Reference

### 7.1 Enums

```python
from enum import Enum

class GPUTier(Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    ULTRA = "ULTRA"

    @classmethod
    def from_string(cls, value: str) -> 'GPUTier':
        try:
            return cls(value)
        except ValueError:
            return cls.NONE

    def __ge__(self, other: 'GPUTier') -> bool:
        order = [self.NONE, self.LOW, self.MEDIUM, self.HIGH, self.ULTRA]
        return order.index(self) >= order.index(other)
```

### 7.2 Dataclasses

```python
from dataclasses import dataclass
from typing import Set, Dict, Any, Tuple

@dataclass
class CapabilityProfile:
    vendor: str
    renderer: str
    opengl_version: Tuple[int, int]
    extensions: Set[str]
    tier: GPUTier
    memory_mb: int
    compute_shader: bool
    features: Dict[str, bool]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vendor": self.vendor,
            "renderer": self.renderer,
            "opengl_version": f"{self.opengl_version[0]}.{self.opengl_version[1]}",
            "extensions": list(self.extensions),
            "tier": self.tier.value,
            "memory_mb": self.memory_mb,
            "compute_shader": self.compute_shader,
            "features": self.features,
        }

@dataclass
class MarketplacePluginDTO:
    id: str
    name: str
    version: str
    description: str
    author: str
    tags: List[str]
    license_type: str
    price_usd: Optional[float]
    subscription_monthly_usd: Optional[float]
    gpu_tier: str
    category: str
    is_installed: bool
    is_compatible: bool
    preview_url: Optional[str]
    repository_url: Optional[str]
```

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (P1-B1) - IN PROGRESS
- [x] Extend `PluginValidator` for new schema ✅ (Completed 2026-02-21)
- [x] Write comprehensive unit tests for validator ✅ (40+ tests in test_plugin_system.py)
- [x] Create plugin manifest examples ✅ (docs/specs/plugin_manifest_examples.md)
- [x] Update documentation with validation rules ✅ (This spec updated)
- [ ] Extend `PluginManifest` with new fields (P1-P2 responsibility)
- [ ] Extend `PluginInfo` with licensing fields (P1-P1 responsibility)
- [ ] Implement `GPUDetector` with tier classification (P1-R2 responsibility)
- [ ] Implement compatibility filtering in `PluginLoader` (P1-P2 responsibility)

### Phase 2: Marketplace Backend (P1-B2) - PENDING
- [ ] Create marketplace API endpoints
- [ ] Implement plugin installation workflow for free plugins
- [ ] Add license status tracking
- [ ] Write integration tests for API

### Phase 3: Marketplace UI (P1-B3) - PENDING
- [ ] Build marketplace frontend component
- [ ] Implement filtering and search
- [ ] Add plugin detail view
- [ ] Connect to backend API
- [ ] Write E2E tests

### Phase 4: Advanced Licensing (P1-B4) - PENDING
- [ ] Burst credits integration
- [ ] Node licensing enforcement
- [ ] Subscription management
- [ ] License key validation
- [ ] Payment gateway integration (stripe/paypal)

---

## 9. Open Questions & Decisions

### Q1: Where to store license state?
**Decision:** Store in user config directory (`~/.vjlive3/licenses.json`) mapping plugin_id → license info (type, expiry, credits_remaining).

### Q2: How to handle plugin updates with licensing changes?
**Decision:** Preserve user's license when updating plugin. If license type changes (e.g., free → paid), grandfather existing installs or require upgrade purchase.

### Q3: Marketplace data source?
**Decision:** Initial implementation uses local plugin directory scanning. Future: remote marketplace server with plugin catalog and download URLs.

### Q4: How to enforce paid plugin restrictions?
**Decision:** At load time, `PluginLoader` checks license status. If not licensed, register as `DISABLED` with error message. UI shows upgrade prompt.

---

## 10. Verification Checklist

### Completed (P1-B1 Core Validation)
- [x] `PluginValidator` validates new fields without breaking old manifests ✅
- [x] Unit tests cover all new validation logic (40+ tests, >80% coverage) ✅
- [x] Backward compatibility: existing plugins load without modification ✅
- [x] Documentation updated with validation rules and examples ✅
- [x] Plugin manifest examples created with 8 comprehensive examples ✅

### Pending (Future Phases)
- [ ] `PluginManifest` extended with new fields (P1-P2)
- [ ] `PluginInfo` includes licensing and compatibility metadata (P1-P1)
- [ ] `GPUDetector` correctly identifies GPU tier (P1-R2)
- [ ] `PluginLoader` filters incompatible plugins by default (P1-P2)
- [ ] `PluginLoader` respects `allow_incompatible` override (P1-P2)
- [ ] Marketplace API returns correct DTOs with filtering (P1-B2)
- [ ] Integration tests verify API endpoints (P1-B2)

---

## 11. References

- Existing Plugin System Spec: [`docs/specs/P1-P1_plugin_registry.md`](docs/specs/P1-P1_plugin_registry.md)
- GPU Context Manager: [`docs/gpu_context.md`](docs/gpu_context.md)
- Source Code:
  - [`src/vjlive3/plugins/registry.py`](src/vjlive3/plugins/registry.py)
  - [`src/vjlive3/plugins/loader.py`](src/vjlive3/plugins/loader.py)
  - [`src/vjlive3/plugins/validator.py`](src/vjlive3/plugins/validator.py)
  - [`src/vjlive3/plugins/api.py`](src/vjlive3/plugins/api.py)

---

**END OF SPECIFICATION**