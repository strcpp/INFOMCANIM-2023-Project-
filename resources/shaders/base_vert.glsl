#version 330

in vec3  in_position;
in vec3  in_normal;
in vec2  in_texcoord_0;;

out vec2 tex_coords;
out vec3 normal;
out vec3 fragPos;

uniform mat4 model;
uniform mat4 projection;
uniform mat4 view;  

void main() {
    mat4 modelView = view * model;
    normal = mat3(transpose(inverse(model))) * normalize(in_normal);
    fragPos = vec3(model * vec4(in_position, 1.0)); 

    gl_Position = projection*view*model*vec4(in_position, 1.0);
    tex_coords = in_texcoord_0;
}