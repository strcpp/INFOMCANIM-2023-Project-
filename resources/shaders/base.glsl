#version 330

#if defined VERTEX_SHADER

in vec3  in_position;
in vec3  in_normal;
in vec2  in_texcoord_0;

// Skinning
in vec4 in_jointsWeight;
in ivec4 in_jointsIdx;

out vec2 tex_coords;
out vec3 interpolated_normal;

uniform mat4 model;
uniform mat4 projection;
uniform mat4 view;

// Skinning
const int MAX_BONES = 100;
uniform int numBones;
uniform int numBoneInfluences;
uniform mat4 jointsMatrices[MAX_BONES];

void main() {
    vec4 totalPosition = vec4(0.0);
    vec4 tempPosition = vec4(in_position, 1.0);

    for (int i = 0; i < numBoneInfluences; i++) {
        int boneIdx = in_jointsIdx[i];
        float weight = in_jointsWeight[i];

        if (boneIdx == -1)
            continue;

        if (boneIdx >= numBones)
            break;

        vec4 localPosition = jointsMatrices[boneIdx] * tempPosition;
        totalPosition += localPosition * weight;
    }

    interpolated_normal = mat3(transpose(inverse(model))) * normalize(in_normal);

    gl_Position = projection * view * model * totalPosition;
    tex_coords = in_texcoord_0;
}

#elif defined FRAGMENT_SHADER

in vec2 tex_coords;
in vec3 interpolated_normal;

out vec4 f_color;

struct Light {
    vec3 position;
    vec3 Ia; 
    vec3 Id; 
    vec3 Is;
};

uniform sampler2D Texture;
uniform Light light;
uniform vec3 camPos;
uniform bool useTexture;

// simple phong model
vec3 calculateLighting(vec3 normal) {
    vec3 ambient = light.Ia;
    
    vec3 dir = normalize(light.position - gl_FragCoord.xyz);
    vec3 diffuse = light.Id * max(0, dot(dir, normal));
    
    vec3 viewDir = normalize(camPos - gl_FragCoord.xyz);
    vec3 reflectDir = reflect(-dir, normal);
    float spec = pow(max(0, dot(viewDir, reflectDir)), 32);
    vec3 specular = light.Is * spec;
    
    // Attenuation
    float constant = 1.0;
    float linear = 0.09;
    float quadratic = 0.032;
    float distance = length(light.position - gl_FragCoord.xyz);
    float attenuation = 1.0 / (constant + linear * distance + quadratic * (distance * distance));
    
    return (ambient + diffuse + specular) * attenuation;
}

void main() {
    vec3 color = vec3(1.0, 0.0, 0.0);    
    if (useTexture) {
        color = texture(Texture, tex_coords).rgb;
    }

    vec3 lighting = calculateLighting(normalize(interpolated_normal));
    color *= lighting;

    f_color = vec4(color, 1.0);
}

#endif
