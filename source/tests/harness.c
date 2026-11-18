// Offline harness for the transpiled gen~ engine.
// usage: harness sr in.f32 out.f32 schedule.txt
//   in/out: interleaved stereo float32; schedule lines: "<frame> <param> <value>"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
void gen_perform(double, double, double*, double*);
int gen_set_param(const char*, double);
void gen_set_sr(double);
void gen_reset(void);
typedef struct { long f; char n[32]; double v; } Ev;
int main(int argc, char** argv) {
    double sr = atof(argv[1]);
    FILE* fi = fopen(argv[2], "rb"); fseek(fi, 0, SEEK_END); long nb = ftell(fi); fseek(fi, 0, SEEK_SET);
    long n = nb / 8; float* in = malloc(nb); fread(in, 1, nb, fi); fclose(fi);
    float* out = malloc(nb);
    Ev* ev = malloc(sizeof(Ev) * 200000); int ne = 0;
    FILE* fs = fopen(argv[4], "r");
    while (ne < 200000 && fscanf(fs, "%ld %31s %lf", &ev[ne].f, ev[ne].n, &ev[ne].v) == 3) ne++;
    fclose(fs);
    gen_reset(); gen_set_sr(sr);
    int k = 0;
    while (k < ne && ev[k].f < 0) { if (gen_set_param(ev[k].n, ev[k].v)) { fprintf(stderr, "bad param %s\n", ev[k].n); return 2; } k++; }
    struct timespec t0, t1; clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long i = 0; i < n; i++) {
        while (k < ne && ev[k].f <= i) { if (gen_set_param(ev[k].n, ev[k].v)) { fprintf(stderr, "bad param %s\n", ev[k].n); return 2; } k++; }
        double a, b; gen_perform(in[2*i], in[2*i+1], &a, &b);
        out[2*i] = (float)a; out[2*i+1] = (float)b;
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double el = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
    FILE* fo = fopen(argv[3], "wb"); fwrite(out, 4, 2*n, fo); fclose(fo);
    printf("%.3f\n", 1e9 * el / n);  // ns per stereo frame
    return 0;
}
