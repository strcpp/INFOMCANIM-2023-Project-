#version 330

#if defined VERTEX_SHADER

in vec3  in_position;
in vec3  in_normal;
in vec2  in_texcoord_0;

// Skinning
in vec4 in_jointsWeight;
in ivec4 in_jointsIdx;

out vec2 tex_coords;
out vec3 normal;
out vec3 fragPos;

uniform mat4 model;
uniform mat4 projection;
uniform mat4 view;

// Skinning
const int MAX_BONES = 100;
uniform int numBones;
uniform int numBoneInfluences;
uniform mat4 jointsMatrices[MAX_BONES];


uniform vec4 jointsRotQuats[MAX_BONES];
uniform vec4 jointsTransQuats[MAX_BONES];

void main() {

    int idx0 = in_jointsIdx[0];
    float w0 = in_jointsWeight[0];
    vec4 r0 = jointsRotQuats[idx0];
    vec4 t0 = jointsTransQuats[idx0];

    vec4 br = r0 * w0;
    vec4 bt = t0 * w0;

    for(int i = 1; i < 4; ++i)
    {
        int idx = in_jointsIdx[i];
        float w = in_jointsWeight[i];

        vec4 r = jointsRotQuats[idx];
        vec4 t = jointsTransQuats[idx];

        if(dot(r, r0) < 0.f)
        {
            w *= -1.f;
        }

        br += r * w;
        bt += t * w;
    }

    // Normalize dual quaternion
    float norm = length(br);
    br = br / norm;
    bt = bt / norm;

    // 3D Vector components
    vec3 v0 = vec3(br[1], br[2], br[3]);
    vec3 ve = vec3(bt[1], bt[2], bt[3]);

    // Translation
    vec3 trans = (ve*br[0] - v0*bt[0] + cross(v0, ve)) * 2.0f;

    // Rotation
    vec3 rot = in_position + cross(v0 * 2.f, cross(v0, in_position) + in_position * br[0]);

    // Result
    vec3 resultPosition = trans + rot;
    resultPosition *= 0.009999999776482582;

    // ----------------
    vec4 resultPosition4 = vec4(resultPosition, 1.0);

    normal = mat3(transpose(inverse(model))) * normalize(in_normal);
    fragPos = vec3(model * resultPosition4);

    gl_Position = projection * view * model * resultPosition4;
    tex_coords = in_texcoord_0;
}

#elif defined FRAGMENT_SHADER

out vec4 f_color;

struct Light {
    vec3 position;
    vec3 Ia; 
    vec3 Id; 
    vec3 Is;
};


in vec2 tex_coords;
in vec3 normal;
in vec3 fragPos;

uniform sampler2D Texture;
uniform Light light;
uniform vec3 camPos;
uniform bool useTexture;

// simple phong model
vec3 calculateLighting() {
    vec3 Normal  = normalize(normal);
    vec3 ambient = light.Ia;
    
    vec3 dir = normalize(light.position - fragPos);
    vec3 diffuse = light.Id * max(0, dot(dir, normal));
    
    vec3 viewDir = normalize(camPos - fragPos);
    vec3 reflectDir = reflect(-dir, Normal);
    float spec = pow(max(0, dot(viewDir, reflectDir)), 32);
    vec3 specular = light.Is * spec;
    
    // Attenuation
    float constant = 1.0;
    float linear = 0.09;
    float quadratic = 0.032;
    float distance = length(light.position - fragPos);
    float attenuation = 1.0 / (constant + linear * distance + quadratic * (distance * distance));
    
    return (ambient + diffuse + specular) * attenuation;
}
void main() {
    float gamma = 2.2;

    vec3 color = vec3(1.0, 0.0, 0.0);    
    if(useTexture) {
        color = texture(Texture, tex_coords).rgb;
    }

    color = pow(color, vec3(gamma));
    color = color * calculateLighting();
    color = pow(color, 1 /  vec3(gamma));

    f_color = vec4(color, 1.0);
}

#endif