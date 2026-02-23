"""
P7-VE44: Vimana Hyperion — geometric sacred craft manifestation.
Ported from VJlive-2 sources.
"""
from typing import Dict, Any
import logging
try:
    import OpenGL.GL as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False
from .api import EffectPlugin, PluginContext
logger = logging.getLogger(__name__)

METADATA = {
    "name": "Vimana Hyperion",
    "description": "Vimana Hyperion — geometric sacred craft manifestation.",
    "version": "1.0.0",
    "plugin_type": "effect",
    "category": "vfx",
    "tags": ['vimana', 'hyperion', 'sacred', 'geometric', 'mystical'],
    "priority": 1,
    "inputs": ["video_in"],
    "outputs": ["video_out"],
    "parameters": [{'name': 'intensity', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'rotation_speed', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'color_hue', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'sacred_scale', 'type': 'float', 'default': 5.0, 'min': 0.0, 'max': 10.0}, {'name': 'aura_glow', 'type': 'float', 'default': 3.0, 'min': 0.0, 'max': 10.0}, {'name': 'mix', 'type': 'float', 'default': 8.0, 'min': 0.0, 'max': 10.0}]
}

VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0); uv = verts[gl_VertexID]*0.5+0.5; }
"""

FRAGMENT_SHADER = """
#version 330 core
in vec2 uv; out vec4 fragColor;
uniform sampler2D tex0; uniform sampler2D prev_tex;
uniform vec2 resolution; uniform float time; uniform float u_mix;
uniform float intensity;  // Effect intensity
uniform float rotation_speed;  // Rotation
uniform float color_hue;  // Hue
uniform float sacred_scale;  // Sacred scale
uniform float aura_glow;  // Aura glow
uniform float mix;  // Output mix
float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p) {
    vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
}
void main() {
    vec4 curr = texture(tex0, uv);
    vec4 prev = texture(prev_tex, uv);
    float d = (intensity/10.0); float fb = 0.0; float fr = 8.0+0.0*10.0;
    float ch = 0.0; float vg = 0.0;
    vec2 du = vec2(noise(uv*fr+vec2(time*0.5))-0.5, noise(uv*fr+vec2(1.3,time*0.4))-0.5)*d*0.05;
    vec4 w = texture(tex0, clamp(uv+du,0.,1.));
    vec3 c = mix(w.rgb, prev.rgb, fb*0.2);
    c.r = texture(tex0, clamp(uv+du+vec2(ch*0.01,0.),0.,1.)).r;
    c.b = texture(tex0, clamp(uv+du-vec2(ch*0.01,0.),0.,1.)).b;
    if(vg>0.){vec2 vc=uv*2.-1.; c*=1.-dot(vc,vc)*vg*0.5;}
    c.r *= 1.+color_hue/10.0*0.2; c.g *= 1.+0.0; c.b *= 1.+0.0;
    fragColor = mix(curr, vec4(clamp(c,0.,1.), curr.a), u_mix);
}
"""

_PARAM_NAMES = ['intensity', 'rotation_speed', 'color_hue', 'sacred_scale', 'aura_glow', 'mix']
_PARAM_DEFAULTS = {'intensity': 5.0, 'rotation_speed': 3.0, 'color_hue': 5.0, 'sacred_scale': 5.0, 'aura_glow': 3.0, 'mix': 8.0}

def _map(val,lo,hi): return lo+(max(0.,min(10.,float(val)))/10.)*(hi-lo)

class VimanaHyperionPlugin(EffectPlugin):
    """Vimana Hyperion — geometric sacred craft manifestation."""
    def __init__(self):
        super().__init__()
        self._mock_mode=not HAS_GL; self.prog=self.vao=0
        self.trail_fbo=self.trail_tex=0; self._w=self._h=0; self._initialized=False
    def get_metadata(self): return METADATA
    def _compile(self,vs,fs):
        v=gl.glCreateShader(gl.GL_VERTEX_SHADER); gl.glShaderSource(v,vs); gl.glCompileShader(v)
        if not gl.glGetShaderiv(v,gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(v))
        f=gl.glCreateShader(gl.GL_FRAGMENT_SHADER); gl.glShaderSource(f,fs); gl.glCompileShader(f)
        if not gl.glGetShaderiv(f,gl.GL_COMPILE_STATUS): raise RuntimeError(gl.glGetShaderInfoLog(f))
        p=gl.glCreateProgram(); gl.glAttachShader(p,v); gl.glAttachShader(p,f); gl.glLinkProgram(p)
        if not gl.glGetProgramiv(p,gl.GL_LINK_STATUS): raise RuntimeError(gl.glGetProgramInfoLog(p))
        gl.glDeleteShader(v); gl.glDeleteShader(f); return p
    def _make_fbo(self,w,h):
        fbo=gl.glGenFramebuffers(1); tex=gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D,tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D,0,gl.GL_RGBA,w,h,0,gl.GL_RGBA,gl.GL_UNSIGNED_BYTE,None)
        for k,v2 in [(gl.GL_TEXTURE_MIN_FILTER,gl.GL_LINEAR),(gl.GL_TEXTURE_MAG_FILTER,gl.GL_LINEAR),
                     (gl.GL_TEXTURE_WRAP_S,gl.GL_CLAMP_TO_EDGE),(gl.GL_TEXTURE_WRAP_T,gl.GL_CLAMP_TO_EDGE)]:
            gl.glTexParameteri(gl.GL_TEXTURE_2D,k,v2)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER,gl.GL_COLOR_ATTACHMENT0,gl.GL_TEXTURE_2D,tex,0)
        gl.glClearColor(0,0,0,0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,0); return fbo,tex
    def initialize(self,context):
        if self._mock_mode or not hasattr(gl,'glCreateShader'):
            self._initialized=True; return True
        try:
            self.prog=self._compile(VERTEX_SHADER,FRAGMENT_SHADER); self.vao=gl.glGenVertexArrays(1)
            self._initialized=True; return True
        except Exception as e:
            logger.error(f"{self.__class__.__name__} init: {e}"); self._mock_mode=True; return False
    def _u(self,n): return gl.glGetUniformLocation(self.prog,n)
    def process_frame(self,input_texture,params,context):
        if not input_texture or input_texture<=0: return 0
        if self._mock_mode or not hasattr(gl,'glCreateShader'):
            if hasattr(context,'outputs'): context.outputs['video_out']=input_texture
            return input_texture
        if not self._initialized: self.initialize(context)
        w=getattr(context,'width',1920); h=getattr(context,'height',1080)
        if w!=self._w or h!=self._h:
            if self.trail_fbo:
                try: gl.glDeleteFramebuffers(1,[self.trail_fbo]); gl.glDeleteTextures(1,[self.trail_tex])
                except Exception: pass
            self.trail_fbo,self.trail_tex=self._make_fbo(w,h); self._w,self._h=w,h
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,self.trail_fbo); gl.glViewport(0,0,w,h)
        gl.glUseProgram(self.prog)
        gl.glActiveTexture(gl.GL_TEXTURE0); gl.glBindTexture(gl.GL_TEXTURE_2D,input_texture); gl.glUniform1i(self._u('tex0'),0)
        gl.glActiveTexture(gl.GL_TEXTURE1); gl.glBindTexture(gl.GL_TEXTURE_2D,self.trail_tex); gl.glUniform1i(self._u('prev_tex'),1)
        gl.glUniform2f(self._u('resolution'),float(w),float(h))
        gl.glUniform1f(self._u('time'),float(getattr(context,'time',0.)))
        gl.glUniform1f(self._u('u_mix'),_map(params.get('mix',8.),0.,1.))
        for p in _PARAM_NAMES:
            gl.glUniform1f(self._u(p),float(params.get(p,_PARAM_DEFAULTS.get(p,5.))))
        gl.glBindVertexArray(self.vao); gl.glDrawArrays(gl.GL_TRIANGLE_STRIP,0,4)
        gl.glBindVertexArray(0); gl.glUseProgram(0); gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,0)
        if hasattr(context,'outputs'): context.outputs['video_out']=self.trail_tex
        return self.trail_tex
    def cleanup(self):
        try:
            if hasattr(gl,'glDeleteProgram') and self.prog: gl.glDeleteProgram(self.prog)
            if hasattr(gl,'glDeleteVertexArrays') and self.vao: gl.glDeleteVertexArrays(1,[self.vao])
            if hasattr(gl,'glDeleteTextures') and self.trail_tex: gl.glDeleteTextures(1,[self.trail_tex])
            if hasattr(gl,'glDeleteFramebuffers') and self.trail_fbo: gl.glDeleteFramebuffers(1,[self.trail_fbo])
        except Exception as e: logger.error(f"{self.__class__.__name__} cleanup: {e}")
        finally: self.prog=self.vao=self.trail_fbo=self.trail_tex=0
