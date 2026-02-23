# Legacy Reference Audit Checklist

## What to Look For in Each Spec

### 1. Legacy Source Identification
- [ ] Clear identification of which legacy codebase (vjlive/ or VJlive-2/) the feature comes from
- [ ] Specific file paths in the legacy codebase
- [ ] Class names and function names from legacy implementation
- [ ] Version differences (v1 vs v2) if applicable

### 2. Key Algorithm Documentation
- [ ] Core algorithms and their implementation details
- [ ] Mathematical formulas or physics simulations
- [ ] Data structures used (arrays, textures, buffers)
- [ ] Performance optimizations and their rationale

### 3. Parameter Mapping
- [ ] Complete parameter registry from legacy
- [ ] Default values and their significance
- [ ] Parameter ranges and constraints
- [ ] Audio reactivity bindings (bass, mid, treble, beat, volume)

### 4. Edge Cases and Error Handling
- [ ] How legacy handled edge cases
- [ ] Performance considerations and optimizations
- [ ] Memory management and cleanup
- [ ] Fallback behaviors

### 5. Porting Decisions
- [ ] What was kept identical from legacy
- [ ] What was modified and why
- [ ] New features or improvements
- [ ] Compatibility considerations

### 6. Technical Implementation Details
- [ ] Shader code references (GLSL, fragment shaders)
- [ ] GPU/CPU data flow
- [ ] Texture usage and formats
- [ ] Frame rate considerations

### 7. Testing and Validation
- [ ] How legacy was tested
- [ ] Performance benchmarks
- [ ] Visual quality comparisons
- [ ] Regression testing approach

## Red Flags (Missing References)
- [ ] No legacy source identified
- [ ] Missing file paths
- [ ] Incomplete parameter documentation
- [ ] No edge case handling
- [ ] Missing performance considerations
- [ ] No porting rationale

## Quality Indicators
- [ ] Comprehensive legacy source mapping
- [ ] Detailed algorithm documentation
- [ ] Complete parameter registry
- [ ] Clear porting decisions
- [ ] Performance and edge case considerations
- [ ] Testing strategy outlined