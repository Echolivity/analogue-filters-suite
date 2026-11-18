// Offline harness for the transpiled gen~ engine.
// usage: harness sr in.f32 out.f32 schedule.txt [key.f32|-] [meters.f32]
//   in/out/key: interleaved stereo float32 (key = external sidechain, gen~ in3/in4)
//   meters: 15 float32 per frame (gen~ out3..out17; v1.6 adds filter OS factor, tube OS factor, fault flag)
//   schedule lines: "<frame> <param> <value>"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
void gen_perform(double, double, double, double, double*);
int gen_set_param(const char*, double);
void gen_set_sr(double);
void gen_reset(void);
typedef struct { long f; char n[32]; double v; } Ev;
static float* load(const char* p, long* nb) {
    FILE* f = fopen(p, "rb"); if (!f) return NULL; fseek(f, 0, SEEK_END); *nb = ftell(f); fseek(f, 0, SEEK_SET);
    float* b = malloc(*nb); if (fread(b, 1, *nb, f) != (size_t)*nb) { fclose(f); return NULL; } fclose(f); return b;
}
int main(int argc, char** argv) {
    double sr = atof(argv[1]);
    long nb; float* in = load(argv[2], &nb); long n = nb / 8;
    long kb = 0; float* key = (argc > 5 && strcmp(argv[5], "-")) ? load(argv[5], &kb) : NULL;
    float* out = malloc(nb);
    float* met = argc > 6 ? malloc(sizeof(float) * 15 * n) : NULL;
    Ev* ev = malloc(sizeof(Ev) * 400000); int ne = 0;
    FILE* fs = fopen(argv[4], "r");
    while (ne < 400000 && fscanf(fs, "%ld %31s %lf", &ev[ne].f, ev[ne].n, &ev[ne].v) == 3) ne++;
    fclose(fs);
    gen_reset(); gen_set_sr(sr);
    int k = 0;
    while (k < ne && ev[k].f < 0) { if (gen_set_param(ev[k].n, ev[k].v)) { fprintf(stderr, "bad param %s\n", ev[k].n); return 2; } k++; }
    double o[17];
    struct timespec t0, t1; clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long i = 0; i < n; i++) {
        while (k < ne && ev[k].f <= i) { if (gen_set_param(ev[k].n, ev[k].v)) { fprintf(stderr, "bad param %s\n", ev[k].n); return 2; } k++; }
        double k1 = 0, k2 = 0;
        if (key && 2 * i + 1 < kb / 4) { k1 = key[2 * i]; k2 = key[2 * i + 1]; }
        for (int j = 0; j < 17; j++) o[j] = 0;
        gen_perform(in[2*i], in[2*i+1], k1, k2, o);
        out[2*i] = (float)o[0]; out[2*i+1] = (float)o[1];
        if (met) for (int j = 0; j < 15; j++) met[15 * i + j] = (float)o[2 + j];
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double el = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
    FILE* fo = fopen(argv[3], "wb"); fwrite(out, 4, 2*n, fo); fclose(fo);
    if (met) { FILE* fm = fopen(argv[6], "wb"); fwrite(met, 4, 15 * n, fm); fclose(fm); }
    printf("%.3f\n", 1e9 * el / n);
    return 0;
}
