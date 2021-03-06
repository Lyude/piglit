// [config]
// expect_result: fail
// glsl_version: 1.30
// require_extensions: GL_MESA_shader_integer_functions
// [end config]

#version 130
#extension GL_MESA_shader_integer_functions: require

in float v1;
in vec2 v2;
in vec3 v3;
in vec4 v4;

// MESA_shader_integer_functions requires at least -0.5 .. 0.5 to be supported.
const vec2 offset = vec2(-0.5, 0.5);

void main()
{
	vec4 res = vec4(0);

	res += vec4(interpolateAtOffset(v1, offset), 1, 1, 1);
	res += vec4(interpolateAtOffset(v2, offset), 1, 1);
	res += vec4(interpolateAtOffset(v3, offset), 1);
	res += interpolateAtOffset(v4, offset);

	gl_FragColor = res;
}
