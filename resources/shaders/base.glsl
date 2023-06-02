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
    vec4 weightedRotQuats =
    jointsRotQuats[int(in_jointsIdx.x)] * in_jointsWeight.x +
    jointsRotQuats[int(in_jointsIdx.y)] * in_jointsWeight.y +
    jointsRotQuats[int(in_jointsIdx.z)] * in_jointsWeight.z +
    jointsRotQuats[int(in_jointsIdx.w)] * in_jointsWeight.w;

  vec4 weightedTransQuats =
    jointsTransQuats[int(in_jointsIdx.x)] * in_jointsWeight.x +
    jointsTransQuats[int(in_jointsIdx.y)] * in_jointsWeight.y +
    jointsTransQuats[int(in_jointsIdx.z)] * in_jointsWeight.z +
    jointsTransQuats[int(in_jointsIdx.w)] * in_jointsWeight.w;

      // Normalize our dual quaternion (necessary for nlerp)
      float xRot = weightedRotQuats[0];
      float yRot = weightedRotQuats[1];
      float zRot = weightedRotQuats[2];
      float wRot = weightedRotQuats[3];
      float magnitude = sqrt(xRot * xRot + yRot * yRot + zRot * zRot + wRot * wRot);
      weightedRotQuats = weightedRotQuats / magnitude;
      weightedTransQuats = weightedTransQuats / magnitude;

      // Convert out dual quaternion in a 4x4 matrix
      //  equation: https://www.cs.utah.edu/~ladislav/kavan07skinning/kavan07skinning.pdf
      float xR = weightedRotQuats[0];
      float yR = weightedRotQuats[1];
      float zR = weightedRotQuats[2];
      float wR = weightedRotQuats[3];

      float xT = weightedTransQuats[0];
      float yT = weightedTransQuats[1];
      float zT = weightedTransQuats[2];
      float wT = weightedTransQuats[3];

      float t0 = 2.0 * (-wT * xR + xT * wR - yT * zR + zT * yR);
      float t1 = 2.0 * (-wT * yR + xT * zR + yT * wR - zT * xR);
      float t2 = 2.0 * (-wT * zR - xT * yR + yT * xR + zT * wR);

      mat4 convertedMatrix = mat4(
          1.0 - (2.0 * yR * yR) - (2.0 * zR * zR),
          (2.0 * xR * yR) + (2.0 * wR * zR),
          (2.0 * xR * zR) - (2.0 * wR * yR),
          0,
          (2.0 * xR * yR) - (2.0 * wR * zR),
          1.0 - (2.0 * xR * xR) - (2.0 * zR * zR),
          (2.0 * yR * zR) + (2.0 * wR * xR),
          0,
          (2.0 * xR * zR) + (2.0 * wR * yR),
          (2.0 * yR * zR) - (2.0 * wR * xR),
          1.0 - (2.0 * xR * xR) - (2.0 * yR * yR),
          0,
          t0,
          t1,
          t2,
          1
          );

    /*
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
    */

    vec4 totalPosition = convertedMatrix * vec4(in_position, 1.0);

    normal = mat3(transpose(inverse(model))) * normalize(in_normal);
    fragPos = vec3(model * totalPosition);

    gl_Position = projection * view * model * totalPosition;
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