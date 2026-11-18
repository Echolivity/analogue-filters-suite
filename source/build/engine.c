#include <math.h>
#include <string.h>

static double g_sr = 48000.0;
static inline double gclamp(double x, double a, double b){ return x < a ? a : (x > b ? b : x); }
static inline double fixdenorm(double x){ return fabs(x) < 1e-30 ? 0.0 : x; }
static double P_l_on = 1.0;
static double P_l_model = 2.0;
static double P_l_cut = 20000.0;
static double P_l_res = 0.0;
static double P_l_slope = 1.0;
static double P_l_drive = 0.0;
static double P_l_comp = 100.0;
static double P_l_char = 0.0;
static double P_h_on = 1.0;
static double P_h_model = 1.0;
static double P_h_cut = 20.0;
static double P_h_res = 0.0;
static double P_h_slope = 0.0;
static double P_h_drive = 0.0;
static double P_h_comp = 100.0;
static double P_h_char = 0.0;
static double P_order_sel = 0.0;
static double P_ovs_sel = 0.0;
static double P_out_db = 0.0;
static double P_softclip = 1.0;
static double Hs_H_l_L_sh_s1a = 0.0;
static double Hs_H_l_L_sh_s2a = 0.0;
static double Hs_H_l_L_sh_ba = 0.0;
static double Hs_H_l_L_sh_s1b = 0.0;
static double Hs_H_l_L_sh_s2b = 0.0;
static double Hs_H_l_L_sh_bb = 0.0;
static double Hs_H_l_L_sh_yp = 0.0;
static double Hs_H_l_R_sh_s1a = 0.0;
static double Hs_H_l_R_sh_s2a = 0.0;
static double Hs_H_l_R_sh_ba = 0.0;
static double Hs_H_l_R_sh_s1b = 0.0;
static double Hs_H_l_R_sh_s2b = 0.0;
static double Hs_H_l_R_sh_bb = 0.0;
static double Hs_H_l_R_sh_yp = 0.0;
static double Hs_H_l_L_k3_s1 = 0.0;
static double Hs_H_l_L_k3_s2 = 0.0;
static double Hs_H_l_L_k3_s3 = 0.0;
static double Hs_H_l_L_k3_yp = 0.0;
static double Hs_H_l_R_k3_s1 = 0.0;
static double Hs_H_l_R_k3_s2 = 0.0;
static double Hs_H_l_R_k3_s3 = 0.0;
static double Hs_H_l_R_k3_yp = 0.0;
static double Hs_H_l_L_ld_s1 = 0.0;
static double Hs_H_l_L_ld_s2 = 0.0;
static double Hs_H_l_L_ld_s3 = 0.0;
static double Hs_H_l_L_ld_s4 = 0.0;
static double Hs_H_l_L_ld_p0 = 0.0;
static double Hs_H_l_L_ld_p1 = 0.0;
static double Hs_H_l_L_ld_p2 = 0.0;
static double Hs_H_l_L_ld_p3 = 0.0;
static double Hs_H_l_L_ld_p4 = 0.0;
static double Hs_H_l_R_ld_s1 = 0.0;
static double Hs_H_l_R_ld_s2 = 0.0;
static double Hs_H_l_R_ld_s3 = 0.0;
static double Hs_H_l_R_ld_s4 = 0.0;
static double Hs_H_l_R_ld_p0 = 0.0;
static double Hs_H_l_R_ld_p1 = 0.0;
static double Hs_H_l_R_ld_p2 = 0.0;
static double Hs_H_l_R_ld_p3 = 0.0;
static double Hs_H_l_R_ld_p4 = 0.0;
static double Hs_H_l_L_st_s1 = 0.0;
static double Hs_H_l_L_st_s2 = 0.0;
static double Hs_H_l_L_st_d1 = 0.0;
static double Hs_H_l_L_st_d2 = 0.0;
static double Hs_H_l_L_st_vb = 0.0;
static double Hs_H_l_R_st_s1 = 0.0;
static double Hs_H_l_R_st_s2 = 0.0;
static double Hs_H_l_R_st_d1 = 0.0;
static double Hs_H_l_R_st_d2 = 0.0;
static double Hs_H_l_R_st_vb = 0.0;
static double Hs_H_l_L_se_s1 = 0.0;
static double Hs_H_l_L_se_s2 = 0.0;
static double Hs_H_l_L_se_hq = 0.0;
static double Hs_H_l_L_se_bq = 0.0;
static double Hs_H_l_R_se_s1 = 0.0;
static double Hs_H_l_R_se_s2 = 0.0;
static double Hs_H_l_R_se_hq = 0.0;
static double Hs_H_l_R_se_bq = 0.0;
static double Hs_H_l_L_di_s1 = 0.0;
static double Hs_H_l_L_di_s2 = 0.0;
static double Hs_H_l_L_di_s3 = 0.0;
static double Hs_H_l_L_di_s4 = 0.0;
static double Hs_H_l_L_di_v1 = 0.0;
static double Hs_H_l_L_di_v2 = 0.0;
static double Hs_H_l_L_di_v3 = 0.0;
static double Hs_H_l_L_di_v4 = 0.0;
static double Hs_H_l_L_di_sf = 0.0;
static double Hs_H_l_L_di_sc = 0.0;
static double Hs_H_l_R_di_s1 = 0.0;
static double Hs_H_l_R_di_s2 = 0.0;
static double Hs_H_l_R_di_s3 = 0.0;
static double Hs_H_l_R_di_s4 = 0.0;
static double Hs_H_l_R_di_v1 = 0.0;
static double Hs_H_l_R_di_v2 = 0.0;
static double Hs_H_l_R_di_v3 = 0.0;
static double Hs_H_l_R_di_v4 = 0.0;
static double Hs_H_l_R_di_sf = 0.0;
static double Hs_H_l_R_di_sc = 0.0;
static double Hs_H_l_L_x0_s1 = 0.0;
static double Hs_H_l_L_x0_s2 = 0.0;
static double Hs_H_l_L_x1_s1 = 0.0;
static double Hs_H_l_L_x1_s2 = 0.0;
static double Hs_H_l_L_x2_s1 = 0.0;
static double Hs_H_l_L_x2_s2 = 0.0;
static double Hs_H_l_R_x0_s1 = 0.0;
static double Hs_H_l_R_x0_s2 = 0.0;
static double Hs_H_l_R_x1_s1 = 0.0;
static double Hs_H_l_R_x1_s2 = 0.0;
static double Hs_H_l_R_x2_s1 = 0.0;
static double Hs_H_l_R_x2_s2 = 0.0;
static double Hs_H_h_L_sh_s1a = 0.0;
static double Hs_H_h_L_sh_s2a = 0.0;
static double Hs_H_h_L_sh_ba = 0.0;
static double Hs_H_h_L_sh_s1b = 0.0;
static double Hs_H_h_L_sh_s2b = 0.0;
static double Hs_H_h_L_sh_bb = 0.0;
static double Hs_H_h_L_sh_yp = 0.0;
static double Hs_H_h_R_sh_s1a = 0.0;
static double Hs_H_h_R_sh_s2a = 0.0;
static double Hs_H_h_R_sh_ba = 0.0;
static double Hs_H_h_R_sh_s1b = 0.0;
static double Hs_H_h_R_sh_s2b = 0.0;
static double Hs_H_h_R_sh_bb = 0.0;
static double Hs_H_h_R_sh_yp = 0.0;
static double Hs_H_h_L_k3_s1 = 0.0;
static double Hs_H_h_L_k3_s2 = 0.0;
static double Hs_H_h_L_k3_s3 = 0.0;
static double Hs_H_h_L_k3_yp = 0.0;
static double Hs_H_h_R_k3_s1 = 0.0;
static double Hs_H_h_R_k3_s2 = 0.0;
static double Hs_H_h_R_k3_s3 = 0.0;
static double Hs_H_h_R_k3_yp = 0.0;
static double Hs_H_h_L_ld_s1 = 0.0;
static double Hs_H_h_L_ld_s2 = 0.0;
static double Hs_H_h_L_ld_s3 = 0.0;
static double Hs_H_h_L_ld_s4 = 0.0;
static double Hs_H_h_L_ld_p0 = 0.0;
static double Hs_H_h_L_ld_p1 = 0.0;
static double Hs_H_h_L_ld_p2 = 0.0;
static double Hs_H_h_L_ld_p3 = 0.0;
static double Hs_H_h_L_ld_p4 = 0.0;
static double Hs_H_h_R_ld_s1 = 0.0;
static double Hs_H_h_R_ld_s2 = 0.0;
static double Hs_H_h_R_ld_s3 = 0.0;
static double Hs_H_h_R_ld_s4 = 0.0;
static double Hs_H_h_R_ld_p0 = 0.0;
static double Hs_H_h_R_ld_p1 = 0.0;
static double Hs_H_h_R_ld_p2 = 0.0;
static double Hs_H_h_R_ld_p3 = 0.0;
static double Hs_H_h_R_ld_p4 = 0.0;
static double Hs_H_h_L_st_s1 = 0.0;
static double Hs_H_h_L_st_s2 = 0.0;
static double Hs_H_h_L_st_d1 = 0.0;
static double Hs_H_h_L_st_d2 = 0.0;
static double Hs_H_h_L_st_vb = 0.0;
static double Hs_H_h_R_st_s1 = 0.0;
static double Hs_H_h_R_st_s2 = 0.0;
static double Hs_H_h_R_st_d1 = 0.0;
static double Hs_H_h_R_st_d2 = 0.0;
static double Hs_H_h_R_st_vb = 0.0;
static double Hs_H_h_L_se_s1 = 0.0;
static double Hs_H_h_L_se_s2 = 0.0;
static double Hs_H_h_L_se_hq = 0.0;
static double Hs_H_h_L_se_bq = 0.0;
static double Hs_H_h_R_se_s1 = 0.0;
static double Hs_H_h_R_se_s2 = 0.0;
static double Hs_H_h_R_se_hq = 0.0;
static double Hs_H_h_R_se_bq = 0.0;
static double Hs_H_h_L_x0_s1 = 0.0;
static double Hs_H_h_L_x0_s2 = 0.0;
static double Hs_H_h_L_x1_s1 = 0.0;
static double Hs_H_h_L_x1_s2 = 0.0;
static double Hs_H_h_L_x2_s1 = 0.0;
static double Hs_H_h_L_x2_s2 = 0.0;
static double Hs_H_h_R_x0_s1 = 0.0;
static double Hs_H_h_R_x0_s2 = 0.0;
static double Hs_H_h_R_x1_s1 = 0.0;
static double Hs_H_h_R_x1_s2 = 0.0;
static double Hs_H_h_R_x2_s1 = 0.0;
static double Hs_H_h_R_x2_s2 = 0.0;
static double Hs_H_os_L_upa0 = 0.0;
static double Hs_H_os_L_upa1 = 0.0;
static double Hs_H_os_L_upa2 = 0.0;
static double Hs_H_os_L_upa3 = 0.0;
static double Hs_H_os_L_upa4 = 0.0;
static double Hs_H_os_L_upa5 = 0.0;
static double Hs_H_os_L_upb0 = 0.0;
static double Hs_H_os_L_upb1 = 0.0;
static double Hs_H_os_L_upb2 = 0.0;
static double Hs_H_os_L_upb3 = 0.0;
static double Hs_H_os_L_upb4 = 0.0;
static double Hs_H_os_L_upb5 = 0.0;
static double Hs_H_os_L_dna0 = 0.0;
static double Hs_H_os_L_dna1 = 0.0;
static double Hs_H_os_L_dna2 = 0.0;
static double Hs_H_os_L_dna3 = 0.0;
static double Hs_H_os_L_dna4 = 0.0;
static double Hs_H_os_L_dna5 = 0.0;
static double Hs_H_os_L_dnb0 = 0.0;
static double Hs_H_os_L_dnb1 = 0.0;
static double Hs_H_os_L_dnb2 = 0.0;
static double Hs_H_os_L_dnb3 = 0.0;
static double Hs_H_os_L_dnb4 = 0.0;
static double Hs_H_os_L_dnb5 = 0.0;
static double Hs_H_dc_L_x = 0.0;
static double Hs_H_dc_L_y = 0.0;
static double Hs_H_os_R_upa0 = 0.0;
static double Hs_H_os_R_upa1 = 0.0;
static double Hs_H_os_R_upa2 = 0.0;
static double Hs_H_os_R_upa3 = 0.0;
static double Hs_H_os_R_upa4 = 0.0;
static double Hs_H_os_R_upa5 = 0.0;
static double Hs_H_os_R_upb0 = 0.0;
static double Hs_H_os_R_upb1 = 0.0;
static double Hs_H_os_R_upb2 = 0.0;
static double Hs_H_os_R_upb3 = 0.0;
static double Hs_H_os_R_upb4 = 0.0;
static double Hs_H_os_R_upb5 = 0.0;
static double Hs_H_os_R_dna0 = 0.0;
static double Hs_H_os_R_dna1 = 0.0;
static double Hs_H_os_R_dna2 = 0.0;
static double Hs_H_os_R_dna3 = 0.0;
static double Hs_H_os_R_dna4 = 0.0;
static double Hs_H_os_R_dna5 = 0.0;
static double Hs_H_os_R_dnb0 = 0.0;
static double Hs_H_os_R_dnb1 = 0.0;
static double Hs_H_os_R_dnb2 = 0.0;
static double Hs_H_os_R_dnb3 = 0.0;
static double Hs_H_os_R_dnb4 = 0.0;
static double Hs_H_os_R_dnb5 = 0.0;
static double Hs_H_dc_R_x = 0.0;
static double Hs_H_dc_R_y = 0.0;
static double Hs_H_l_lc = 14.287712379549449;
static double Hs_H_l_rz = 0.0;
static double Hs_H_l_drv = 0.0;
static double Hs_H_l_cmp = 1.0;
static double Hs_H_l_chr = 0.0;
static double Hs_H_l_en = 1.0;
static double Hs_H_l_ti = 1.0;
static double Hs_H_l_w0 = 1.0;
static double Hs_H_l_w1 = 0.0;
static double Hs_H_l_w2 = 0.0;
static double Hs_H_l_w3 = 0.0;
static double Hs_H_l_cur = 2.0;
static double Hs_H_l_prev = 2.0;
static double Hs_H_l_fade = 1.0;
static double Hs_H_h_lc = 4.321928094887363;
static double Hs_H_h_rz = 0.0;
static double Hs_H_h_drv = 0.0;
static double Hs_H_h_cmp = 1.0;
static double Hs_H_h_chr = 0.0;
static double Hs_H_h_en = 1.0;
static double Hs_H_h_ti = 0.0;
static double Hs_H_h_w0 = 1.0;
static double Hs_H_h_w1 = 0.0;
static double Hs_H_h_w2 = 0.0;
static double Hs_H_h_w3 = 0.0;
static double Hs_H_h_cur = 1.0;
static double Hs_H_h_prev = 1.0;
static double Hs_H_h_fade = 1.0;
static double Hs_H_cur_order = 0.0;
static double Hs_H_cur_os = 0.0;
static double Hs_H_duck = 1.0;
static double Hs_H_og = 1.0;
static double Hs_H_init = 0.0;
static void F_f_op(double a_x, double a_s, double a_G, double* o0, double* o1);
static double F_f_tg(double a_v);
static double F_f_dg(double a_v);
static double F_f_ag(double a_v);
static double F_f_asym(double a_x);
static void F_f_svf(double a_x, double a_s1, double a_s2, double a_g, double a_R, double* o0, double* o1, double* o2, double* o3, double* o4);
static void F_f_tri4(double a_d1, double a_d2, double a_d3, double a_d4, double a_B1, double a_C1, double a_A2, double a_B2, double a_C2, double a_A3, double a_B3, double a_C3, double a_A4, double a_B4, double* o0, double* o1, double* o2, double* o3);
static void F_f_sherman(double a_x, double a_s1a, double a_s2a, double a_ba, double a_s1b, double a_s2b, double a_bb, double a_yp, double a_g, double a_R1, double a_Rt, double a_fb, double a_ti, double a_hp, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5, double* o6, double* o7, double* o8);
static void F_f_k35lp(double a_x, double a_s1, double a_s2, double a_s3, double a_yp, double a_g, double a_K0, double a_L, double* o0, double* o1, double* o2, double* o3, double* o4);
static void F_f_k35hp(double a_x, double a_s1, double a_s2, double a_s3, double a_yp, double a_g, double a_K0, double a_L, double* o0, double* o1, double* o2, double* o3, double* o4);
static void F_f_ladder(double a_x, double a_s1, double a_s2, double a_s3, double a_s4, double a_p0, double a_p1, double a_p2, double a_p3, double a_p4, double a_g, double a_k, double a_bc, double a_hs, double a_hp, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5, double* o6, double* o7, double* o8, double* o9, double* o10);
static void F_f_steiner(double a_xl, double a_xb, double a_xh, double a_s1, double a_s2, double a_d1p, double a_d2p, double a_vbp, double a_g, double a_K, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5);
static void F_f_sem(double a_x, double a_s1, double a_s2, double a_hpp, double a_bpp, double a_g, double a_R, double a_m, double a_hp, double* o0, double* o1, double* o2, double* o3, double* o4);
static void F_f_diode(double a_x, double a_s1, double a_s2, double a_s3, double a_s4, double a_v1p, double a_v2p, double a_v3p, double a_v4p, double a_sf, double a_sc, double a_g, double a_k, double a_Gf, double a_bc, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5, double* o6, double* o7, double* o8, double* o9, double* o10);
static void F_f_ap5(double a_x, double a_z0, double a_z1, double a_z2, double a_z3, double a_z4, double a_z5, double a_c1, double a_c2, double a_c3, double a_c4, double a_c5, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5, double* o6);
static void F_f_op(double a_x, double a_s, double a_G, double* o0, double* o1) {
    double v_lp = 0.0, v_v = 0.0;
    v_v = ((a_x - a_s) * a_G);
    v_lp = (v_v + a_s);
    { double _r0 = v_lp, _r1 = (v_lp + v_v);
      *o0 = _r0;
      *o1 = _r1;
      return; }
}
static double F_f_tg(double a_v) {
    double v_a = 0.0, v_r = 0.0;
    v_a = fabs(a_v);
    v_r = (1.0 - ((v_a * v_a) * 0.333333333));
    if ((((double)((v_a) > (0.001)))) != 0.0) {
        v_r = (tanh(a_v) / a_v);
    }
    return v_r;
}
static double F_f_dg(double a_v) {
    double v_a = 0.0, v_r = 0.0;
    v_a = fabs(a_v);
    v_r = (1.0 - (0.3363755443363322 * a_v));
    if ((((double)((v_a) > (0.001)))) != 0.0) {
        v_r = ((tanh((a_v + 0.35)) - 0.3363755443363322) / (a_v * 0.8868514931724362));
    }
    return fmax(v_r, 0.0);
}
static double F_f_ag(double a_v) {
    return (1.0 / sqrt((1.0 + (a_v * a_v))));
}
static double F_f_asym(double a_x) {
    return ((tanh((a_x + 0.35)) - 0.3363755443363322) / 0.8868514931724362);
}
static void F_f_svf(double a_x, double a_s1, double a_s2, double a_g, double a_R, double* o0, double* o1, double* o2, double* o3, double* o4) {
    double v_b = 0.0, v_h = 0.0, v_l = 0.0;
    v_h = (((a_x - (((2.0 * a_R) + a_g) * a_s1)) - a_s2) / ((1.0 + ((2.0 * a_R) * a_g)) + (a_g * a_g)));
    v_b = ((a_g * v_h) + a_s1);
    v_l = ((a_g * v_b) + a_s2);
    { double _r0 = v_h, _r1 = v_b, _r2 = v_l, _r3 = ((a_g * v_h) + v_b), _r4 = ((a_g * v_b) + v_l);
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      return; }
}
static void F_f_tri4(double a_d1, double a_d2, double a_d3, double a_d4, double a_B1, double a_C1, double a_A2, double a_B2, double a_C2, double a_A3, double a_B3, double a_C3, double a_A4, double a_B4, double* o0, double* o1, double* o2, double* o3) {
    double v_c1 = 0.0, v_c2 = 0.0, v_c3 = 0.0, v_e1 = 0.0, v_e2 = 0.0, v_e3 = 0.0, v_m2 = 0.0, v_m3 = 0.0, v_y1 = 0.0, v_y2 = 0.0, v_y3 = 0.0, v_y4 = 0.0;
    v_c1 = (a_C1 / a_B1);
    v_e1 = (a_d1 / a_B1);
    v_m2 = (a_B2 - (a_A2 * v_c1));
    v_c2 = (a_C2 / v_m2);
    v_e2 = ((a_d2 - (a_A2 * v_e1)) / v_m2);
    v_m3 = (a_B3 - (a_A3 * v_c2));
    v_c3 = (a_C3 / v_m3);
    v_e3 = ((a_d3 - (a_A3 * v_e2)) / v_m3);
    v_y4 = ((a_d4 - (a_A4 * v_e3)) / (a_B4 - (a_A4 * v_c3)));
    v_y3 = (v_e3 - (v_c3 * v_y4));
    v_y2 = (v_e2 - (v_c2 * v_y3));
    v_y1 = (v_e1 - (v_c1 * v_y2));
    { double _r0 = v_y1, _r1 = v_y2, _r2 = v_y3, _r3 = v_y4;
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      return; }
}
static void F_f_sherman(double a_x, double a_s1a, double a_s2a, double a_ba, double a_s1b, double a_s2b, double a_bb, double a_yp, double a_g, double a_R1, double a_Rt, double a_fb, double a_ti, double a_hp, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5, double* o6, double* o7, double* o8) {
    double v_Ra = 0.0, v_Rb = 0.0, v_b1 = 0.0, v_b2 = 0.0, v_h1 = 0.0, v_h2 = 0.0, v_i2 = 0.0, v_l1 = 0.0, v_l2 = 0.0, v_n1a = 0.0, v_n1b = 0.0, v_n2a = 0.0, v_n2b = 0.0, v_o1 = 0.0, v_o2 = 0.0, v_u = 0.0, v_ynext = 0.0;
    v_u = (F_f_asym((1.6 * (a_x + (a_fb * a_yp)))) * 0.625);
    v_Ra = (1.0 - ((1.0 - a_R1) * F_f_tg(a_ba)));
    { double _t0, _t1, _t2, _t3, _t4; F_f_svf(v_u, a_s1a, a_s2a, a_g, v_Ra, &_t0, &_t1, &_t2, &_t3, &_t4);
      v_h1 = _t0;
      v_b1 = _t1;
      v_l1 = _t2;
      v_n1a = _t3;
      v_n2a = _t4;
    }
    v_o1 = ((((double)((a_hp) > (0.5)))) != 0.0 ? (v_h1) : (v_l1));
    v_Rb = (1.0 - ((1.0 - a_Rt) * F_f_ag((a_bb * 2.0))));
    v_i2 = (v_u + (a_ti * (v_o1 - v_u)));
    { double _t5, _t6, _t7, _t8, _t9; F_f_svf(v_i2, a_s1b, a_s2b, a_g, v_Rb, &_t5, &_t6, &_t7, &_t8, &_t9);
      v_h2 = _t5;
      v_b2 = _t6;
      v_l2 = _t7;
      v_n1b = _t8;
      v_n2b = _t9;
    }
    v_o2 = ((((double)((a_hp) > (0.5)))) != 0.0 ? (v_h2) : (v_l2));
    v_ynext = tanh(v_o2);
    { double _r0 = v_o2, _r1 = v_o2, _r2 = fixdenorm(v_n1a), _r3 = fixdenorm(v_n2a), _r4 = v_b1, _r5 = fixdenorm(v_n1b), _r6 = fixdenorm(v_n2b), _r7 = v_b2, _r8 = v_ynext;
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      *o5 = _r5;
      *o6 = _r6;
      *o7 = _r7;
      *o8 = _r8;
      return; }
}
static void F_f_k35lp(double a_x, double a_s1, double a_s2, double a_s3, double a_yp, double a_g, double a_K0, double a_L, double* o0, double* o1, double* o2, double* o3, double* o4) {
    double v_G = 0.0, v_K = 0.0, v_ig = 0.0, v_l3 = 0.0, v_n1 = 0.0, v_n2 = 0.0, v_n3 = 0.0, v_u = 0.0, v_y = 0.0, v_y1 = 0.0;
    v_G = (a_g / (1.0 + a_g));
    v_ig = (1.0 / (1.0 + a_g));
    v_K = (a_K0 * F_f_tg(((a_K0 * a_yp) / a_L)));
    { double _t0, _t1; F_f_op(a_x, a_s1, v_G, &_t0, &_t1);
      v_y1 = _t0;
      v_n1 = _t1;
    }
    v_u = ((v_y1 + (v_ig * (((v_K * v_ig) * a_s2) - a_s3))) / (1.0 - ((v_K * v_G) * v_ig)));
    v_u = (0.85 * tanh((v_u * 1.17647058824)));
    { double _t2, _t3; F_f_op(v_u, a_s2, v_G, &_t2, &_t3);
      v_y = _t2;
      v_n2 = _t3;
    }
    { double _t4, _t5; F_f_op((v_K * v_y), a_s3, v_G, &_t4, &_t5);
      v_l3 = _t4;
      v_n3 = _t5;
    }
    { double _r0 = v_y, _r1 = fixdenorm(v_n1), _r2 = fixdenorm(v_n2), _r3 = fixdenorm(v_n3), _r4 = v_y;
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      return; }
}
static void F_f_k35hp(double a_x, double a_s1, double a_s2, double a_s3, double a_yp, double a_g, double a_K0, double a_L, double* o0, double* o1, double* o2, double* o3, double* o4) {
    double v_G = 0.0, v_K = 0.0, v_ig = 0.0, v_l1 = 0.0, v_l2 = 0.0, v_l3 = 0.0, v_n1 = 0.0, v_n2 = 0.0, v_n3 = 0.0, v_u = 0.0, v_y = 0.0, v_y1 = 0.0;
    v_G = (a_g / (1.0 + a_g));
    v_ig = (1.0 / (1.0 + a_g));
    v_K = (a_K0 * F_f_tg(((a_K0 * a_yp) / a_L)));
    { double _t0, _t1; F_f_op(a_x, a_s1, v_G, &_t0, &_t1);
      v_l1 = _t0;
      v_n1 = _t1;
    }
    v_y1 = (a_x - v_l1);
    v_u = ((v_y1 + (v_ig * (a_s3 - ((v_G * v_K) * a_s2)))) / (1.0 - ((v_K * v_G) * v_ig)));
    v_u = (0.85 * tanh((v_u * 1.17647058824)));
    { double _t2, _t3; F_f_op(v_u, a_s2, v_G, &_t2, &_t3);
      v_l2 = _t2;
      v_n2 = _t3;
    }
    v_y = (v_u - v_l2);
    { double _t4, _t5; F_f_op((v_K * v_y), a_s3, v_G, &_t4, &_t5);
      v_l3 = _t4;
      v_n3 = _t5;
    }
    { double _r0 = v_y, _r1 = fixdenorm(v_n1), _r2 = fixdenorm(v_n2), _r3 = fixdenorm(v_n3), _r4 = v_y;
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      return; }
}
static void F_f_ladder(double a_x, double a_s1, double a_s2, double a_s3, double a_s4, double a_p0, double a_p1, double a_p2, double a_p3, double a_p4, double a_g, double a_k, double a_bc, double a_hs, double a_hp, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5, double* o6, double* o7, double* o8, double* o9, double* o10) {
    double v_G1 = 0.0, v_G2 = 0.0, v_G3 = 0.0, v_G4 = 0.0, v_S = 0.0, v_T0 = 0.0, v_T1 = 0.0, v_T2 = 0.0, v_T3 = 0.0, v_T4 = 0.0, v_i1 = 0.0, v_i2 = 0.0, v_i3 = 0.0, v_i4 = 0.0, v_o12 = 0.0, v_o24 = 0.0, v_u = 0.0, v_y1 = 0.0, v_y2 = 0.0, v_y3 = 0.0, v_y4 = 0.0;
    v_T0 = F_f_tg((1.4 * a_p0));
    v_T1 = F_f_tg(((1.4 * a_hs) * a_p1));
    v_T2 = F_f_tg(((1.4 * a_hs) * a_p2));
    v_T3 = F_f_tg(((1.4 * a_hs) * a_p3));
    v_T4 = F_f_tg(((1.4 * a_hs) * a_p4));
    v_i1 = (1.0 / (1.0 + (a_g * v_T1)));
    v_i2 = (1.0 / (1.0 + (a_g * v_T2)));
    v_i3 = (1.0 / (1.0 + (a_g * v_T3)));
    v_i4 = (1.0 / (1.0 + (a_g * v_T4)));
    v_G1 = ((a_g * v_T0) * v_i1);
    v_G2 = ((a_g * v_T1) * v_i2);
    v_G3 = ((a_g * v_T2) * v_i3);
    v_G4 = ((a_g * v_T3) * v_i4);
    v_S = (((((((v_G2 * v_G3) * v_G4) * a_s1) * v_i1) + (((v_G3 * v_G4) * a_s2) * v_i2)) + ((v_G4 * a_s3) * v_i3)) + (a_s4 * v_i4));
    v_u = (((a_x * (1.0 + (a_k * a_bc))) - (a_k * v_S)) / (1.0 + ((((a_k * v_G1) * v_G2) * v_G3) * v_G4)));
    v_y1 = ((v_G1 * v_u) + (a_s1 * v_i1));
    v_y2 = ((v_G2 * v_y1) + (a_s2 * v_i2));
    v_y3 = ((v_G3 * v_y2) + (a_s3 * v_i3));
    v_y4 = ((v_G4 * v_y3) + (a_s4 * v_i4));
    v_o12 = v_y2;
    v_o24 = v_y4;
    if ((((double)((a_hp) > (0.5)))) != 0.0) {
        v_o12 = ((v_u - (2.0 * v_y1)) + v_y2);
        v_o24 = ((((v_u - (4.0 * v_y1)) + (6.0 * v_y2)) - (4.0 * v_y3)) + v_y4);
    }
    { double _r0 = v_o12, _r1 = v_o24, _r2 = fixdenorm(((2.0 * v_y1) - a_s1)), _r3 = fixdenorm(((2.0 * v_y2) - a_s2)), _r4 = fixdenorm(((2.0 * v_y3) - a_s3)), _r5 = fixdenorm(((2.0 * v_y4) - a_s4)), _r6 = v_u, _r7 = v_y1, _r8 = v_y2, _r9 = v_y3, _r10 = v_y4;
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      *o5 = _r5;
      *o6 = _r6;
      *o7 = _r7;
      *o8 = _r8;
      *o9 = _r9;
      *o10 = _r10;
      return; }
}
static void F_f_steiner(double a_xl, double a_xb, double a_xh, double a_s1, double a_s2, double a_d1p, double a_d2p, double a_vbp, double a_g, double a_K, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5) {
    double v_Ke = 0.0, v_a11 = 0.0, v_a12 = 0.0, v_a21 = 0.0, v_a22 = 0.0, v_b1 = 0.0, v_b2 = 0.0, v_c2 = 0.0, v_idet = 0.0, v_q1 = 0.0, v_q2 = 0.0, v_t1 = 0.0, v_t2 = 0.0, v_vA = 0.0, v_vB = 0.0;
    v_t1 = F_f_tg((a_d1p * 0.7));
    v_t2 = F_f_tg((a_d2p * 0.7));
    v_Ke = (a_K * F_f_ag(((a_K * a_vbp) * 0.7)));
    v_a11 = (1.0 + (a_g * (v_t1 + v_t2)));
    v_a12 = ((-a_g) * ((v_t1 * v_Ke) + (v_t2 * (v_Ke - 1.0))));
    v_a21 = (a_g * v_t2);
    v_a22 = (1.0 - ((a_g * v_t2) * (v_Ke - 1.0)));
    v_c2 = ((a_g * v_t2) * (((v_Ke - 1.0) * a_xh) + a_xb));
    v_b1 = ((((a_g * v_t1) * (((v_Ke * a_xh) + a_xb) - a_xl)) + v_c2) + a_s1);
    v_b2 = (v_c2 + a_s2);
    v_idet = (1.0 / ((v_a11 * v_a22) - (v_a12 * v_a21)));
    v_q1 = (((v_b1 * v_a22) - (v_a12 * v_b2)) * v_idet);
    v_q2 = (((v_a11 * v_b2) - (v_a21 * v_b1)) * v_idet);
    v_vB = (v_q2 + a_xh);
    v_vA = (((v_Ke * v_vB) + a_xb) - v_q1);
    { double _r0 = (v_Ke * v_vB), _r1 = fixdenorm(((2.0 * v_q1) - a_s1)), _r2 = fixdenorm(((2.0 * v_q2) - a_s2)), _r3 = (a_xl - v_vA), _r4 = (v_vA - v_vB), _r5 = v_vB;
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      *o5 = _r5;
      return; }
}
static void F_f_sem(double a_x, double a_s1, double a_s2, double a_hpp, double a_bpp, double a_g, double a_R, double a_m, double a_hp, double* o0, double* o1, double* o2, double* o3, double* o4) {
    double v_b = 0.0, v_g1 = 0.0, v_g2 = 0.0, v_h = 0.0, v_l = 0.0, v_u = 0.0, v_y = 0.0;
    v_u = (2.0 * tanh((0.5 * a_x)));
    v_g1 = (a_g * F_f_tg((a_hpp * 0.6)));
    v_g2 = (a_g * F_f_tg((a_bpp * 0.6)));
    v_h = (((v_u - (((2.0 * a_R) + v_g2) * a_s1)) - a_s2) / ((1.0 + ((2.0 * a_R) * v_g1)) + (v_g1 * v_g2)));
    v_b = ((v_g1 * v_h) + a_s1);
    v_l = ((v_g2 * v_b) + a_s2);
    v_y = ((((double)((a_hp) > (0.5)))) != 0.0 ? ((v_h + (a_m * v_l))) : ((v_l + (a_m * v_h))));
    { double _r0 = v_y, _r1 = fixdenorm(((2.0 * v_b) - a_s1)), _r2 = fixdenorm(((2.0 * v_l) - a_s2)), _r3 = v_h, _r4 = v_b;
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      return; }
}
static void F_f_diode(double a_x, double a_s1, double a_s2, double a_s3, double a_s4, double a_v1p, double a_v2p, double a_v3p, double a_v4p, double a_sf, double a_sc, double a_g, double a_k, double a_Gf, double a_bc, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5, double* o6, double* o7, double* o8, double* o9, double* o10) {
    double v_A2 = 0.0, v_A3 = 0.0, v_A4 = 0.0, v_B1 = 0.0, v_B2 = 0.0, v_B3 = 0.0, v_B4 = 0.0, v_C1 = 0.0, v_C2 = 0.0, v_C3 = 0.0, v_a1 = 0.0, v_a2 = 0.0, v_a3 = 0.0, v_a4 = 0.0, v_b1 = 0.0, v_b2 = 0.0, v_b3 = 0.0, v_b4 = 0.0, v_igf = 0.0, v_lc = 0.0, v_lf = 0.0, v_nsc = 0.0, v_nsf = 0.0, v_t1 = 0.0, v_t2 = 0.0, v_t3 = 0.0, v_t4 = 0.0, v_u = 0.0, v_xc = 0.0, v_xi = 0.0, v_y1 = 0.0, v_y2 = 0.0, v_y3 = 0.0, v_y4 = 0.0;
    v_t1 = F_f_tg((0.5 * (a_v1p - a_v2p)));
    v_t2 = F_f_tg((0.5 * (a_v2p - a_v3p)));
    v_t3 = F_f_tg((0.5 * (a_v3p - a_v4p)));
    v_t4 = F_f_tg((0.5 * a_v4p));
    v_B1 = (1.0 + ((2.0 * a_g) * v_t1));
    v_C1 = (((-2.0) * a_g) * v_t1);
    v_A2 = ((-a_g) * v_t1);
    v_B2 = (1.0 + (a_g * (v_t1 + v_t2)));
    v_C2 = ((-a_g) * v_t2);
    v_A3 = ((-a_g) * v_t2);
    v_B3 = (1.0 + (a_g * (v_t2 + v_t3)));
    v_C3 = ((-a_g) * v_t3);
    v_A4 = ((-a_g) * v_t3);
    v_B4 = (1.0 + (a_g * (v_t3 + v_t4)));
    { double _t0, _t1, _t2, _t3; F_f_tri4((2.0 * a_g), 0.0, 0.0, 0.0, v_B1, v_C1, v_A2, v_B2, v_C2, v_A3, v_B3, v_C3, v_A4, v_B4, &_t0, &_t1, &_t2, &_t3);
      v_a1 = _t0;
      v_a2 = _t1;
      v_a3 = _t2;
      v_a4 = _t3;
    }
    { double _t4, _t5, _t6, _t7; F_f_tri4(a_s1, a_s2, a_s3, a_s4, v_B1, v_C1, v_A2, v_B2, v_C2, v_A3, v_B3, v_C3, v_A4, v_B4, &_t4, &_t5, &_t6, &_t7);
      v_b1 = _t4;
      v_b2 = _t5;
      v_b3 = _t6;
      v_b4 = _t7;
    }
    v_xi = tanh(a_x);
    { double _t8, _t9; F_f_op(v_xi, a_sc, a_Gf, &_t8, &_t9);
      v_lc = _t8;
      v_nsc = _t9;
    }
    v_xc = (v_xi + ((a_k * a_bc) * (v_xi - v_lc)));
    v_igf = (1.0 - a_Gf);
    v_u = ((v_xc - ((a_k * v_igf) * (v_b4 - a_sf))) / (1.0 + ((a_k * v_igf) * v_a4)));
    v_u = (2.0 * tanh((0.5 * v_u)));
    v_y1 = (v_b1 + (v_u * v_a1));
    v_y2 = (v_b2 + (v_u * v_a2));
    v_y3 = (v_b3 + (v_u * v_a3));
    v_y4 = (v_b4 + (v_u * v_a4));
    { double _t10, _t11; F_f_op(v_y4, a_sf, a_Gf, &_t10, &_t11);
      v_lf = _t10;
      v_nsf = _t11;
    }
    { double _r0 = v_y4, _r1 = fixdenorm(((2.0 * v_y1) - a_s1)), _r2 = fixdenorm(((2.0 * v_y2) - a_s2)), _r3 = fixdenorm(((2.0 * v_y3) - a_s3)), _r4 = fixdenorm(((2.0 * v_y4) - a_s4)), _r5 = v_y1, _r6 = v_y2, _r7 = v_y3, _r8 = v_y4, _r9 = fixdenorm(v_nsf), _r10 = fixdenorm(v_nsc);
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      *o5 = _r5;
      *o6 = _r6;
      *o7 = _r7;
      *o8 = _r8;
      *o9 = _r9;
      *o10 = _r10;
      return; }
}
static void F_f_ap5(double a_x, double a_z0, double a_z1, double a_z2, double a_z3, double a_z4, double a_z5, double a_c1, double a_c2, double a_c3, double a_c4, double a_c5, double* o0, double* o1, double* o2, double* o3, double* o4, double* o5, double* o6) {
    double v_y1 = 0.0, v_y2 = 0.0, v_y3 = 0.0, v_y4 = 0.0, v_y5 = 0.0;
    v_y1 = ((a_c1 * (a_x - a_z1)) + a_z0);
    v_y2 = ((a_c2 * (v_y1 - a_z2)) + a_z1);
    v_y3 = ((a_c3 * (v_y2 - a_z3)) + a_z2);
    v_y4 = ((a_c4 * (v_y3 - a_z4)) + a_z3);
    v_y5 = ((a_c5 * (v_y4 - a_z5)) + a_z4);
    { double _r0 = v_y5, _r1 = a_x, _r2 = v_y1, _r3 = v_y2, _r4 = v_y3, _r5 = v_y4, _r6 = v_y5;
      *o0 = _r0;
      *o1 = _r1;
      *o2 = _r2;
      *o3 = _r3;
      *o4 = _r4;
      *o5 = _r5;
      *o6 = _r6;
      return; }
}
void gen_perform(double in1, double in2, double* out1, double* out2) {
    double v_a_cut = 0.0, v_a_mix = 0.0, v_a_par = 0.0, v_aq = 0.0, v_cfg_o = 0.0, v_cfg_s = 0.0, v_cur_order = 0.0, v_cur_os = 0.0, v_dc_L_x = 0.0, v_dc_L_y = 0.0, v_dc_R_x = 0.0, v_dc_R_y = 0.0, v_dcr = 0.0, v_dstep = 0.0, v_duck = 0.0, v_dy_L = 0.0, v_dy_R = 0.0, v_e0 = 0.0, v_e1 = 0.0, v_e2 = 0.0, v_e3 = 0.0, v_eb = 0.0, v_eh = 0.0, v_el = 0.0, v_fs = 0.0, v_fso = 0.0, v_fstep = 0.0, v_h_L_k3_s1 = 0.0, v_h_L_k3_s2 = 0.0, v_h_L_k3_s3 = 0.0, v_h_L_k3_yp = 0.0, v_h_L_ld_p0 = 0.0, v_h_L_ld_p1 = 0.0, v_h_L_ld_p2 = 0.0, v_h_L_ld_p3 = 0.0, v_h_L_ld_p4 = 0.0, v_h_L_ld_s1 = 0.0, v_h_L_ld_s2 = 0.0, v_h_L_ld_s3 = 0.0, v_h_L_ld_s4 = 0.0, v_h_L_se_bq = 0.0, v_h_L_se_hq = 0.0, v_h_L_se_s1 = 0.0, v_h_L_se_s2 = 0.0, v_h_L_sh_ba = 0.0, v_h_L_sh_bb = 0.0, v_h_L_sh_s1a = 0.0, v_h_L_sh_s1b = 0.0, v_h_L_sh_s2a = 0.0, v_h_L_sh_s2b = 0.0, v_h_L_sh_yp = 0.0, v_h_L_st_d1 = 0.0, v_h_L_st_d2 = 0.0, v_h_L_st_s1 = 0.0, v_h_L_st_s2 = 0.0, v_h_L_st_vb = 0.0, v_h_L_x0_s1 = 0.0, v_h_L_x0_s2 = 0.0, v_h_L_x1_s1 = 0.0, v_h_L_x1_s2 = 0.0, v_h_L_x2_s1 = 0.0, v_h_L_x2_s2 = 0.0, v_h_R_k3_s1 = 0.0, v_h_R_k3_s2 = 0.0, v_h_R_k3_s3 = 0.0, v_h_R_k3_yp = 0.0, v_h_R_ld_p0 = 0.0, v_h_R_ld_p1 = 0.0, v_h_R_ld_p2 = 0.0, v_h_R_ld_p3 = 0.0, v_h_R_ld_p4 = 0.0, v_h_R_ld_s1 = 0.0, v_h_R_ld_s2 = 0.0, v_h_R_ld_s3 = 0.0, v_h_R_ld_s4 = 0.0, v_h_R_se_bq = 0.0, v_h_R_se_hq = 0.0, v_h_R_se_s1 = 0.0, v_h_R_se_s2 = 0.0, v_h_R_sh_ba = 0.0, v_h_R_sh_bb = 0.0, v_h_R_sh_s1a = 0.0, v_h_R_sh_s1b = 0.0, v_h_R_sh_s2a = 0.0, v_h_R_sh_s2b = 0.0, v_h_R_sh_yp = 0.0, v_h_R_st_d1 = 0.0, v_h_R_st_d2 = 0.0, v_h_R_st_s1 = 0.0, v_h_R_st_s2 = 0.0, v_h_R_st_vb = 0.0, v_h_R_x0_s1 = 0.0, v_h_R_x0_s2 = 0.0, v_h_R_x1_s1 = 0.0, v_h_R_x1_s2 = 0.0, v_h_R_x2_s1 = 0.0, v_h_R_x2_s2 = 0.0, v_h_ak3 = 0.0, v_h_ald = 0.0, v_h_ase = 0.0, v_h_ash = 0.0, v_h_ast = 0.0, v_h_chr = 0.0, v_h_cmp = 0.0, v_h_cur = 0.0, v_h_d = 0.0, v_h_det = 0.0, v_h_drv = 0.0, v_h_en = 0.0, v_h_ent = 0.0, v_h_fade = 0.0, v_h_fc = 0.0, v_h_fcc = 0.0, v_h_gw = 0.0, v_h_gx = 0.0, v_h_id = 0.0, v_h_k3_K = 0.0, v_h_k3_L = 0.0, v_h_k3_g = 0.0, v_h_lc = 0.0, v_h_ld_bc = 0.0, v_h_ld_g = 0.0, v_h_ld_hs = 0.0, v_h_ld_k = 0.0, v_h_mk3 = 0.0, v_h_mld = 0.0, v_h_mse = 0.0, v_h_msel = 0.0, v_h_msh = 0.0, v_h_mst = 0.0, v_h_n12 = 0.0, v_h_next = 0.0, v_h_osc = 0.0, v_h_prev = 0.0, v_h_run = 0.0, v_h_rz = 0.0, v_h_se_R = 0.0, v_h_se_g = 0.0, v_h_sh_R = 0.0, v_h_sh_R1 = 0.0, v_h_sh_fb = 0.0, v_h_sh_g = 0.0, v_h_ssel = 0.0, v_h_st_K = 0.0, v_h_st_g = 0.0, v_h_st_kd = 0.0, v_h_ti = 0.0, v_h_tit = 0.0, v_h_w0 = 0.0, v_h_w1 = 0.0, v_h_w2 = 0.0, v_h_w3 = 0.0, v_h_wet = 0.0, v_h_xa = 0.0, v_h_xb = 0.0, v_h_xc = 0.0, v_hb_L = 0.0, v_hb_R = 0.0, v_hi_L = 0.0, v_hi_R = 0.0, v_hya_L = 0.0, v_hya_R = 0.0, v_hyb_L = 0.0, v_hyb_R = 0.0, v_l_L_di_s1 = 0.0, v_l_L_di_s2 = 0.0, v_l_L_di_s3 = 0.0, v_l_L_di_s4 = 0.0, v_l_L_di_sc = 0.0, v_l_L_di_sf = 0.0, v_l_L_di_v1 = 0.0, v_l_L_di_v2 = 0.0, v_l_L_di_v3 = 0.0, v_l_L_di_v4 = 0.0, v_l_L_k3_s1 = 0.0, v_l_L_k3_s2 = 0.0, v_l_L_k3_s3 = 0.0, v_l_L_k3_yp = 0.0, v_l_L_ld_p0 = 0.0, v_l_L_ld_p1 = 0.0, v_l_L_ld_p2 = 0.0, v_l_L_ld_p3 = 0.0, v_l_L_ld_p4 = 0.0, v_l_L_ld_s1 = 0.0, v_l_L_ld_s2 = 0.0, v_l_L_ld_s3 = 0.0, v_l_L_ld_s4 = 0.0, v_l_L_se_bq = 0.0, v_l_L_se_hq = 0.0, v_l_L_se_s1 = 0.0, v_l_L_se_s2 = 0.0, v_l_L_sh_ba = 0.0, v_l_L_sh_bb = 0.0, v_l_L_sh_s1a = 0.0, v_l_L_sh_s1b = 0.0, v_l_L_sh_s2a = 0.0, v_l_L_sh_s2b = 0.0, v_l_L_sh_yp = 0.0, v_l_L_st_d1 = 0.0, v_l_L_st_d2 = 0.0, v_l_L_st_s1 = 0.0, v_l_L_st_s2 = 0.0, v_l_L_st_vb = 0.0, v_l_L_x0_s1 = 0.0, v_l_L_x0_s2 = 0.0, v_l_L_x1_s1 = 0.0, v_l_L_x1_s2 = 0.0, v_l_L_x2_s1 = 0.0, v_l_L_x2_s2 = 0.0, v_l_R_di_s1 = 0.0, v_l_R_di_s2 = 0.0, v_l_R_di_s3 = 0.0, v_l_R_di_s4 = 0.0, v_l_R_di_sc = 0.0, v_l_R_di_sf = 0.0, v_l_R_di_v1 = 0.0, v_l_R_di_v2 = 0.0, v_l_R_di_v3 = 0.0, v_l_R_di_v4 = 0.0, v_l_R_k3_s1 = 0.0, v_l_R_k3_s2 = 0.0, v_l_R_k3_s3 = 0.0, v_l_R_k3_yp = 0.0, v_l_R_ld_p0 = 0.0, v_l_R_ld_p1 = 0.0, v_l_R_ld_p2 = 0.0, v_l_R_ld_p3 = 0.0, v_l_R_ld_p4 = 0.0, v_l_R_ld_s1 = 0.0, v_l_R_ld_s2 = 0.0, v_l_R_ld_s3 = 0.0, v_l_R_ld_s4 = 0.0, v_l_R_se_bq = 0.0, v_l_R_se_hq = 0.0, v_l_R_se_s1 = 0.0, v_l_R_se_s2 = 0.0, v_l_R_sh_ba = 0.0, v_l_R_sh_bb = 0.0, v_l_R_sh_s1a = 0.0, v_l_R_sh_s1b = 0.0, v_l_R_sh_s2a = 0.0, v_l_R_sh_s2b = 0.0, v_l_R_sh_yp = 0.0, v_l_R_st_d1 = 0.0, v_l_R_st_d2 = 0.0, v_l_R_st_s1 = 0.0, v_l_R_st_s2 = 0.0, v_l_R_st_vb = 0.0, v_l_R_x0_s1 = 0.0, v_l_R_x0_s2 = 0.0, v_l_R_x1_s1 = 0.0, v_l_R_x1_s2 = 0.0, v_l_R_x2_s1 = 0.0, v_l_R_x2_s2 = 0.0, v_l_adi = 0.0, v_l_ak3 = 0.0, v_l_ald = 0.0, v_l_ase = 0.0, v_l_ash = 0.0, v_l_ast = 0.0, v_l_chr = 0.0, v_l_cmp = 0.0, v_l_cur = 0.0, v_l_d = 0.0, v_l_det = 0.0, v_l_di_Gf = 0.0, v_l_di_g = 0.0, v_l_di_gf = 0.0, v_l_di_k = 0.0, v_l_drv = 0.0, v_l_en = 0.0, v_l_ent = 0.0, v_l_fade = 0.0, v_l_fc = 0.0, v_l_fcc = 0.0, v_l_gw = 0.0, v_l_gx = 0.0, v_l_id = 0.0, v_l_k3_K = 0.0, v_l_k3_L = 0.0, v_l_k3_g = 0.0, v_l_lc = 0.0, v_l_ld_bc = 0.0, v_l_ld_g = 0.0, v_l_ld_hs = 0.0, v_l_ld_k = 0.0, v_l_mdi = 0.0, v_l_mk3 = 0.0, v_l_mld = 0.0, v_l_mse = 0.0, v_l_msel = 0.0, v_l_msh = 0.0, v_l_mst = 0.0, v_l_n12 = 0.0, v_l_next = 0.0, v_l_osc = 0.0, v_l_prev = 0.0, v_l_run = 0.0, v_l_rz = 0.0, v_l_se_R = 0.0, v_l_se_g = 0.0, v_l_sh_R = 0.0, v_l_sh_R1 = 0.0, v_l_sh_fb = 0.0, v_l_sh_g = 0.0, v_l_ssel = 0.0, v_l_st_K = 0.0, v_l_st_g = 0.0, v_l_st_kd = 0.0, v_l_ti = 0.0, v_l_tit = 0.0, v_l_w0 = 0.0, v_l_w1 = 0.0, v_l_w2 = 0.0, v_l_w3 = 0.0, v_l_wet = 0.0, v_l_xa = 0.0, v_l_xb = 0.0, v_l_xc = 0.0, v_lb_L = 0.0, v_lb_R = 0.0, v_li_L = 0.0, v_li_R = 0.0, v_lsrc_L = 0.0, v_lsrc_R = 0.0, v_lya_L = 0.0, v_lya_R = 0.0, v_lyb_L = 0.0, v_lyb_R = 0.0, v_new_order = 0.0, v_new_os = 0.0, v_o1 = 0.0, v_o12 = 0.0, v_o24 = 0.0, v_og = 0.0, v_os_L_dna0 = 0.0, v_os_L_dna1 = 0.0, v_os_L_dna2 = 0.0, v_os_L_dna3 = 0.0, v_os_L_dna4 = 0.0, v_os_L_dna5 = 0.0, v_os_L_dnb0 = 0.0, v_os_L_dnb1 = 0.0, v_os_L_dnb2 = 0.0, v_os_L_dnb3 = 0.0, v_os_L_dnb4 = 0.0, v_os_L_dnb5 = 0.0, v_os_L_upa0 = 0.0, v_os_L_upa1 = 0.0, v_os_L_upa2 = 0.0, v_os_L_upa3 = 0.0, v_os_L_upa4 = 0.0, v_os_L_upa5 = 0.0, v_os_L_upb0 = 0.0, v_os_L_upb1 = 0.0, v_os_L_upb2 = 0.0, v_os_L_upb3 = 0.0, v_os_L_upb4 = 0.0, v_os_L_upb5 = 0.0, v_os_R_dna0 = 0.0, v_os_R_dna1 = 0.0, v_os_R_dna2 = 0.0, v_os_R_dna3 = 0.0, v_os_R_dna4 = 0.0, v_os_R_dna5 = 0.0, v_os_R_dnb0 = 0.0, v_os_R_dnb1 = 0.0, v_os_R_dnb2 = 0.0, v_os_R_dnb3 = 0.0, v_os_R_dnb4 = 0.0, v_os_R_dnb5 = 0.0, v_os_R_upa0 = 0.0, v_os_R_upa1 = 0.0, v_os_R_upa2 = 0.0, v_os_R_upa3 = 0.0, v_os_R_upa4 = 0.0, v_os_R_upa5 = 0.0, v_os_R_upb0 = 0.0, v_os_R_upb1 = 0.0, v_os_R_upb2 = 0.0, v_os_R_upb3 = 0.0, v_os_R_upb4 = 0.0, v_os_R_upb5 = 0.0, v_ovs = 0.0, v_pa = 0.0, v_pb = 0.0, v_pend = 0.0, v_q_L = 0.0, v_q_R = 0.0, v_rst = 0.0, v_wet_L = 0.0, v_wet_R = 0.0, v_x_L = 0.0, v_x_R = 0.0, v_xa_L = 0.0, v_xa_R = 0.0, v_xb_L = 0.0, v_xb_R = 0.0, v_y_L = 0.0, v_y_R = 0.0, v_za_L = 0.0, v_za_R = 0.0, v_zb_L = 0.0, v_zb_R = 0.0;
    v_fs = g_sr;
    v_cur_order = Hs_H_cur_order;
    v_cur_os = Hs_H_cur_os;
    v_ovs = ((((double)((v_cur_os) > (0.5)))) != 0.0 ? (2.0) : (1.0));
    v_fso = (v_fs * v_ovs);
    v_a_cut = (1.0 - exp(((-1.0) / (0.006 * v_fs))));
    v_a_par = (1.0 - exp(((-1.0) / (0.015 * v_fs))));
    v_a_mix = (1.0 - exp(((-1.0) / (0.010 * v_fs))));
    v_fstep = (1.0 / (0.025 * v_fs));
    v_dstep = (1.0 / (0.004 * v_fs));
    v_x_L = in1;
    v_x_R = in2;
    v_l_L_sh_s1a = Hs_H_l_L_sh_s1a;
    v_l_L_sh_s2a = Hs_H_l_L_sh_s2a;
    v_l_L_sh_ba = Hs_H_l_L_sh_ba;
    v_l_L_sh_s1b = Hs_H_l_L_sh_s1b;
    v_l_L_sh_s2b = Hs_H_l_L_sh_s2b;
    v_l_L_sh_bb = Hs_H_l_L_sh_bb;
    v_l_L_sh_yp = Hs_H_l_L_sh_yp;
    v_l_R_sh_s1a = Hs_H_l_R_sh_s1a;
    v_l_R_sh_s2a = Hs_H_l_R_sh_s2a;
    v_l_R_sh_ba = Hs_H_l_R_sh_ba;
    v_l_R_sh_s1b = Hs_H_l_R_sh_s1b;
    v_l_R_sh_s2b = Hs_H_l_R_sh_s2b;
    v_l_R_sh_bb = Hs_H_l_R_sh_bb;
    v_l_R_sh_yp = Hs_H_l_R_sh_yp;
    v_l_L_k3_s1 = Hs_H_l_L_k3_s1;
    v_l_L_k3_s2 = Hs_H_l_L_k3_s2;
    v_l_L_k3_s3 = Hs_H_l_L_k3_s3;
    v_l_L_k3_yp = Hs_H_l_L_k3_yp;
    v_l_R_k3_s1 = Hs_H_l_R_k3_s1;
    v_l_R_k3_s2 = Hs_H_l_R_k3_s2;
    v_l_R_k3_s3 = Hs_H_l_R_k3_s3;
    v_l_R_k3_yp = Hs_H_l_R_k3_yp;
    v_l_L_ld_s1 = Hs_H_l_L_ld_s1;
    v_l_L_ld_s2 = Hs_H_l_L_ld_s2;
    v_l_L_ld_s3 = Hs_H_l_L_ld_s3;
    v_l_L_ld_s4 = Hs_H_l_L_ld_s4;
    v_l_L_ld_p0 = Hs_H_l_L_ld_p0;
    v_l_L_ld_p1 = Hs_H_l_L_ld_p1;
    v_l_L_ld_p2 = Hs_H_l_L_ld_p2;
    v_l_L_ld_p3 = Hs_H_l_L_ld_p3;
    v_l_L_ld_p4 = Hs_H_l_L_ld_p4;
    v_l_R_ld_s1 = Hs_H_l_R_ld_s1;
    v_l_R_ld_s2 = Hs_H_l_R_ld_s2;
    v_l_R_ld_s3 = Hs_H_l_R_ld_s3;
    v_l_R_ld_s4 = Hs_H_l_R_ld_s4;
    v_l_R_ld_p0 = Hs_H_l_R_ld_p0;
    v_l_R_ld_p1 = Hs_H_l_R_ld_p1;
    v_l_R_ld_p2 = Hs_H_l_R_ld_p2;
    v_l_R_ld_p3 = Hs_H_l_R_ld_p3;
    v_l_R_ld_p4 = Hs_H_l_R_ld_p4;
    v_l_L_st_s1 = Hs_H_l_L_st_s1;
    v_l_L_st_s2 = Hs_H_l_L_st_s2;
    v_l_L_st_d1 = Hs_H_l_L_st_d1;
    v_l_L_st_d2 = Hs_H_l_L_st_d2;
    v_l_L_st_vb = Hs_H_l_L_st_vb;
    v_l_R_st_s1 = Hs_H_l_R_st_s1;
    v_l_R_st_s2 = Hs_H_l_R_st_s2;
    v_l_R_st_d1 = Hs_H_l_R_st_d1;
    v_l_R_st_d2 = Hs_H_l_R_st_d2;
    v_l_R_st_vb = Hs_H_l_R_st_vb;
    v_l_L_se_s1 = Hs_H_l_L_se_s1;
    v_l_L_se_s2 = Hs_H_l_L_se_s2;
    v_l_L_se_hq = Hs_H_l_L_se_hq;
    v_l_L_se_bq = Hs_H_l_L_se_bq;
    v_l_R_se_s1 = Hs_H_l_R_se_s1;
    v_l_R_se_s2 = Hs_H_l_R_se_s2;
    v_l_R_se_hq = Hs_H_l_R_se_hq;
    v_l_R_se_bq = Hs_H_l_R_se_bq;
    v_l_L_di_s1 = Hs_H_l_L_di_s1;
    v_l_L_di_s2 = Hs_H_l_L_di_s2;
    v_l_L_di_s3 = Hs_H_l_L_di_s3;
    v_l_L_di_s4 = Hs_H_l_L_di_s4;
    v_l_L_di_v1 = Hs_H_l_L_di_v1;
    v_l_L_di_v2 = Hs_H_l_L_di_v2;
    v_l_L_di_v3 = Hs_H_l_L_di_v3;
    v_l_L_di_v4 = Hs_H_l_L_di_v4;
    v_l_L_di_sf = Hs_H_l_L_di_sf;
    v_l_L_di_sc = Hs_H_l_L_di_sc;
    v_l_R_di_s1 = Hs_H_l_R_di_s1;
    v_l_R_di_s2 = Hs_H_l_R_di_s2;
    v_l_R_di_s3 = Hs_H_l_R_di_s3;
    v_l_R_di_s4 = Hs_H_l_R_di_s4;
    v_l_R_di_v1 = Hs_H_l_R_di_v1;
    v_l_R_di_v2 = Hs_H_l_R_di_v2;
    v_l_R_di_v3 = Hs_H_l_R_di_v3;
    v_l_R_di_v4 = Hs_H_l_R_di_v4;
    v_l_R_di_sf = Hs_H_l_R_di_sf;
    v_l_R_di_sc = Hs_H_l_R_di_sc;
    v_l_L_x0_s1 = Hs_H_l_L_x0_s1;
    v_l_L_x0_s2 = Hs_H_l_L_x0_s2;
    v_l_L_x1_s1 = Hs_H_l_L_x1_s1;
    v_l_L_x1_s2 = Hs_H_l_L_x1_s2;
    v_l_L_x2_s1 = Hs_H_l_L_x2_s1;
    v_l_L_x2_s2 = Hs_H_l_L_x2_s2;
    v_l_R_x0_s1 = Hs_H_l_R_x0_s1;
    v_l_R_x0_s2 = Hs_H_l_R_x0_s2;
    v_l_R_x1_s1 = Hs_H_l_R_x1_s1;
    v_l_R_x1_s2 = Hs_H_l_R_x1_s2;
    v_l_R_x2_s1 = Hs_H_l_R_x2_s1;
    v_l_R_x2_s2 = Hs_H_l_R_x2_s2;
    v_h_L_sh_s1a = Hs_H_h_L_sh_s1a;
    v_h_L_sh_s2a = Hs_H_h_L_sh_s2a;
    v_h_L_sh_ba = Hs_H_h_L_sh_ba;
    v_h_L_sh_s1b = Hs_H_h_L_sh_s1b;
    v_h_L_sh_s2b = Hs_H_h_L_sh_s2b;
    v_h_L_sh_bb = Hs_H_h_L_sh_bb;
    v_h_L_sh_yp = Hs_H_h_L_sh_yp;
    v_h_R_sh_s1a = Hs_H_h_R_sh_s1a;
    v_h_R_sh_s2a = Hs_H_h_R_sh_s2a;
    v_h_R_sh_ba = Hs_H_h_R_sh_ba;
    v_h_R_sh_s1b = Hs_H_h_R_sh_s1b;
    v_h_R_sh_s2b = Hs_H_h_R_sh_s2b;
    v_h_R_sh_bb = Hs_H_h_R_sh_bb;
    v_h_R_sh_yp = Hs_H_h_R_sh_yp;
    v_h_L_k3_s1 = Hs_H_h_L_k3_s1;
    v_h_L_k3_s2 = Hs_H_h_L_k3_s2;
    v_h_L_k3_s3 = Hs_H_h_L_k3_s3;
    v_h_L_k3_yp = Hs_H_h_L_k3_yp;
    v_h_R_k3_s1 = Hs_H_h_R_k3_s1;
    v_h_R_k3_s2 = Hs_H_h_R_k3_s2;
    v_h_R_k3_s3 = Hs_H_h_R_k3_s3;
    v_h_R_k3_yp = Hs_H_h_R_k3_yp;
    v_h_L_ld_s1 = Hs_H_h_L_ld_s1;
    v_h_L_ld_s2 = Hs_H_h_L_ld_s2;
    v_h_L_ld_s3 = Hs_H_h_L_ld_s3;
    v_h_L_ld_s4 = Hs_H_h_L_ld_s4;
    v_h_L_ld_p0 = Hs_H_h_L_ld_p0;
    v_h_L_ld_p1 = Hs_H_h_L_ld_p1;
    v_h_L_ld_p2 = Hs_H_h_L_ld_p2;
    v_h_L_ld_p3 = Hs_H_h_L_ld_p3;
    v_h_L_ld_p4 = Hs_H_h_L_ld_p4;
    v_h_R_ld_s1 = Hs_H_h_R_ld_s1;
    v_h_R_ld_s2 = Hs_H_h_R_ld_s2;
    v_h_R_ld_s3 = Hs_H_h_R_ld_s3;
    v_h_R_ld_s4 = Hs_H_h_R_ld_s4;
    v_h_R_ld_p0 = Hs_H_h_R_ld_p0;
    v_h_R_ld_p1 = Hs_H_h_R_ld_p1;
    v_h_R_ld_p2 = Hs_H_h_R_ld_p2;
    v_h_R_ld_p3 = Hs_H_h_R_ld_p3;
    v_h_R_ld_p4 = Hs_H_h_R_ld_p4;
    v_h_L_st_s1 = Hs_H_h_L_st_s1;
    v_h_L_st_s2 = Hs_H_h_L_st_s2;
    v_h_L_st_d1 = Hs_H_h_L_st_d1;
    v_h_L_st_d2 = Hs_H_h_L_st_d2;
    v_h_L_st_vb = Hs_H_h_L_st_vb;
    v_h_R_st_s1 = Hs_H_h_R_st_s1;
    v_h_R_st_s2 = Hs_H_h_R_st_s2;
    v_h_R_st_d1 = Hs_H_h_R_st_d1;
    v_h_R_st_d2 = Hs_H_h_R_st_d2;
    v_h_R_st_vb = Hs_H_h_R_st_vb;
    v_h_L_se_s1 = Hs_H_h_L_se_s1;
    v_h_L_se_s2 = Hs_H_h_L_se_s2;
    v_h_L_se_hq = Hs_H_h_L_se_hq;
    v_h_L_se_bq = Hs_H_h_L_se_bq;
    v_h_R_se_s1 = Hs_H_h_R_se_s1;
    v_h_R_se_s2 = Hs_H_h_R_se_s2;
    v_h_R_se_hq = Hs_H_h_R_se_hq;
    v_h_R_se_bq = Hs_H_h_R_se_bq;
    v_h_L_x0_s1 = Hs_H_h_L_x0_s1;
    v_h_L_x0_s2 = Hs_H_h_L_x0_s2;
    v_h_L_x1_s1 = Hs_H_h_L_x1_s1;
    v_h_L_x1_s2 = Hs_H_h_L_x1_s2;
    v_h_L_x2_s1 = Hs_H_h_L_x2_s1;
    v_h_L_x2_s2 = Hs_H_h_L_x2_s2;
    v_h_R_x0_s1 = Hs_H_h_R_x0_s1;
    v_h_R_x0_s2 = Hs_H_h_R_x0_s2;
    v_h_R_x1_s1 = Hs_H_h_R_x1_s1;
    v_h_R_x1_s2 = Hs_H_h_R_x1_s2;
    v_h_R_x2_s1 = Hs_H_h_R_x2_s1;
    v_h_R_x2_s2 = Hs_H_h_R_x2_s2;
    v_os_L_upa0 = Hs_H_os_L_upa0;
    v_os_L_upa1 = Hs_H_os_L_upa1;
    v_os_L_upa2 = Hs_H_os_L_upa2;
    v_os_L_upa3 = Hs_H_os_L_upa3;
    v_os_L_upa4 = Hs_H_os_L_upa4;
    v_os_L_upa5 = Hs_H_os_L_upa5;
    v_os_L_upb0 = Hs_H_os_L_upb0;
    v_os_L_upb1 = Hs_H_os_L_upb1;
    v_os_L_upb2 = Hs_H_os_L_upb2;
    v_os_L_upb3 = Hs_H_os_L_upb3;
    v_os_L_upb4 = Hs_H_os_L_upb4;
    v_os_L_upb5 = Hs_H_os_L_upb5;
    v_os_L_dna0 = Hs_H_os_L_dna0;
    v_os_L_dna1 = Hs_H_os_L_dna1;
    v_os_L_dna2 = Hs_H_os_L_dna2;
    v_os_L_dna3 = Hs_H_os_L_dna3;
    v_os_L_dna4 = Hs_H_os_L_dna4;
    v_os_L_dna5 = Hs_H_os_L_dna5;
    v_os_L_dnb0 = Hs_H_os_L_dnb0;
    v_os_L_dnb1 = Hs_H_os_L_dnb1;
    v_os_L_dnb2 = Hs_H_os_L_dnb2;
    v_os_L_dnb3 = Hs_H_os_L_dnb3;
    v_os_L_dnb4 = Hs_H_os_L_dnb4;
    v_os_L_dnb5 = Hs_H_os_L_dnb5;
    v_dc_L_x = Hs_H_dc_L_x;
    v_dc_L_y = Hs_H_dc_L_y;
    v_os_R_upa0 = Hs_H_os_R_upa0;
    v_os_R_upa1 = Hs_H_os_R_upa1;
    v_os_R_upa2 = Hs_H_os_R_upa2;
    v_os_R_upa3 = Hs_H_os_R_upa3;
    v_os_R_upa4 = Hs_H_os_R_upa4;
    v_os_R_upa5 = Hs_H_os_R_upa5;
    v_os_R_upb0 = Hs_H_os_R_upb0;
    v_os_R_upb1 = Hs_H_os_R_upb1;
    v_os_R_upb2 = Hs_H_os_R_upb2;
    v_os_R_upb3 = Hs_H_os_R_upb3;
    v_os_R_upb4 = Hs_H_os_R_upb4;
    v_os_R_upb5 = Hs_H_os_R_upb5;
    v_os_R_dna0 = Hs_H_os_R_dna0;
    v_os_R_dna1 = Hs_H_os_R_dna1;
    v_os_R_dna2 = Hs_H_os_R_dna2;
    v_os_R_dna3 = Hs_H_os_R_dna3;
    v_os_R_dna4 = Hs_H_os_R_dna4;
    v_os_R_dna5 = Hs_H_os_R_dna5;
    v_os_R_dnb0 = Hs_H_os_R_dnb0;
    v_os_R_dnb1 = Hs_H_os_R_dnb1;
    v_os_R_dnb2 = Hs_H_os_R_dnb2;
    v_os_R_dnb3 = Hs_H_os_R_dnb3;
    v_os_R_dnb4 = Hs_H_os_R_dnb4;
    v_os_R_dnb5 = Hs_H_os_R_dnb5;
    v_dc_R_x = Hs_H_dc_R_x;
    v_dc_R_y = Hs_H_dc_R_y;
    v_l_lc = (Hs_H_l_lc + (v_a_cut * (log2(gclamp(P_l_cut, 20.0, 20000.0)) - Hs_H_l_lc)));
    v_l_rz = (Hs_H_l_rz + (v_a_par * ((gclamp(P_l_res, 0.0, 100.0) * 0.01) - Hs_H_l_rz)));
    v_l_drv = (Hs_H_l_drv + (v_a_par * ((gclamp(P_l_drive, 0.0, 100.0) * 0.01) - Hs_H_l_drv)));
    v_l_cmp = (Hs_H_l_cmp + (v_a_par * ((gclamp(P_l_comp, 0.0, 100.0) * 0.01) - Hs_H_l_cmp)));
    v_l_chr = (Hs_H_l_chr + (v_a_par * ((gclamp(P_l_char, 0.0, 100.0) * 0.01) - Hs_H_l_chr)));
    v_l_fc = exp2(v_l_lc);
    v_l_fcc = fmin(v_l_fc, (0.45 * v_fso));
    v_l_gw = tan(((M_PI * v_l_fcc) / v_fso));
    v_l_ent = ((((double)((P_l_on) > (0.5)))) != 0.0 ? (1.0) : (0.0));
    v_l_en = (Hs_H_l_en + (v_a_mix * (v_l_ent - Hs_H_l_en)));
    if ((((double)((((double)((v_l_ent) < (0.5)))) && (((double)((v_l_en) < (0.0001))))))) != 0.0) {
        v_l_en = 0.0;
    }
    if ((((double)((((double)((v_l_ent) > (0.5)))) && (((double)((v_l_en) > (0.9999))))))) != 0.0) {
        v_l_en = 1.0;
    }
    v_l_det = gclamp(((20000.0 - v_l_fc) * 0.00025), 0.0, 1.0);
    v_l_wet = (v_l_en * v_l_det);
    v_l_run = ((((double)((v_l_wet) > (0.0)))) != 0.0 ? (1.0) : (0.0));
    v_l_d = (0.25 * exp2((5.0 * v_l_drv)));
    v_l_id = (1.0 / v_l_d);
    v_l_osc = (v_l_id * exp2(((5.0 * v_l_drv) * (1.0 - (0.5 * v_l_cmp)))));
    v_l_msel = gclamp(floor((P_l_model + 0.5)), 0.0, 5.0);
    v_l_cur = Hs_H_l_cur;
    v_l_prev = Hs_H_l_prev;
    v_l_fade = Hs_H_l_fade;
    if ((((double)((v_l_msel) != (v_l_cur)))) != 0.0) {
        v_l_prev = v_l_cur;
        v_l_cur = v_l_msel;
        v_l_fade = 0.0;
    }
    v_l_fade = fmin(1.0, (v_l_fade + v_fstep));
    v_l_ssel = gclamp(floor((P_l_slope + 0.5)), 0.0, 3.0);
    v_l_tit = ((((double)((v_l_ssel) > (0.5)))) != 0.0 ? (1.0) : (0.0));
    v_l_n12 = ((((double)((((double)((((double)((v_l_cur) == (1.0)))) || (((double)((v_l_cur) == (3.0))))))) || (((double)((v_l_cur) == (4.0))))))) != 0.0 ? (1.0) : (0.0));
    v_l_next = ((((double)((v_l_n12) > (0.5)))) != 0.0 ? (v_l_ssel) : (fmax(0.0, (v_l_ssel - 1.0))));
    v_l_ti = (Hs_H_l_ti + (v_a_mix * (v_l_tit - Hs_H_l_ti)));
    v_l_w0 = (Hs_H_l_w0 + (v_a_mix * (((((double)((v_l_next) == (0.0)))) != 0.0 ? (1.0) : (0.0)) - Hs_H_l_w0)));
    v_l_w1 = (Hs_H_l_w1 + (v_a_mix * (((((double)((v_l_next) == (1.0)))) != 0.0 ? (1.0) : (0.0)) - Hs_H_l_w1)));
    v_l_w2 = (Hs_H_l_w2 + (v_a_mix * (((((double)((v_l_next) == (2.0)))) != 0.0 ? (1.0) : (0.0)) - Hs_H_l_w2)));
    v_l_w3 = (Hs_H_l_w3 + (v_a_mix * (((((double)((v_l_next) == (3.0)))) != 0.0 ? (1.0) : (0.0)) - Hs_H_l_w3)));
    v_l_xa = ((((double)((((v_l_w1 + v_l_w2) + v_l_w3)) > (0.00001)))) != 0.0 ? (1.0) : (0.0));
    v_l_xb = ((((double)(((v_l_w2 + v_l_w3)) > (0.00001)))) != 0.0 ? (1.0) : (0.0));
    v_l_xc = ((((double)((v_l_w3) > (0.00001)))) != 0.0 ? (1.0) : (0.0));
    v_l_gx = v_l_gw;
    v_l_ash = ((((double)((((double)((v_l_run) > (0.5)))) && (((double)((((double)((v_l_cur) == (0.0)))) || (((double)((((double)((v_l_prev) == (0.0)))) && (((double)((v_l_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_l_msh = (((((double)((v_l_cur) == (0.0)))) != 0.0 ? (v_l_fade) : (0.0)) + ((((double)((((double)((v_l_prev) == (0.0)))) && (((double)((v_l_cur) != (0.0))))))) != 0.0 ? ((1.0 - v_l_fade)) : (0.0)));
    v_l_ak3 = ((((double)((((double)((v_l_run) > (0.5)))) && (((double)((((double)((v_l_cur) == (1.0)))) || (((double)((((double)((v_l_prev) == (1.0)))) && (((double)((v_l_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_l_mk3 = (((((double)((v_l_cur) == (1.0)))) != 0.0 ? (v_l_fade) : (0.0)) + ((((double)((((double)((v_l_prev) == (1.0)))) && (((double)((v_l_cur) != (1.0))))))) != 0.0 ? ((1.0 - v_l_fade)) : (0.0)));
    v_l_ald = ((((double)((((double)((v_l_run) > (0.5)))) && (((double)((((double)((v_l_cur) == (2.0)))) || (((double)((((double)((v_l_prev) == (2.0)))) && (((double)((v_l_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_l_mld = (((((double)((v_l_cur) == (2.0)))) != 0.0 ? (v_l_fade) : (0.0)) + ((((double)((((double)((v_l_prev) == (2.0)))) && (((double)((v_l_cur) != (2.0))))))) != 0.0 ? ((1.0 - v_l_fade)) : (0.0)));
    v_l_ast = ((((double)((((double)((v_l_run) > (0.5)))) && (((double)((((double)((v_l_cur) == (3.0)))) || (((double)((((double)((v_l_prev) == (3.0)))) && (((double)((v_l_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_l_mst = (((((double)((v_l_cur) == (3.0)))) != 0.0 ? (v_l_fade) : (0.0)) + ((((double)((((double)((v_l_prev) == (3.0)))) && (((double)((v_l_cur) != (3.0))))))) != 0.0 ? ((1.0 - v_l_fade)) : (0.0)));
    v_l_ase = ((((double)((((double)((v_l_run) > (0.5)))) && (((double)((((double)((v_l_cur) == (4.0)))) || (((double)((((double)((v_l_prev) == (4.0)))) && (((double)((v_l_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_l_mse = (((((double)((v_l_cur) == (4.0)))) != 0.0 ? (v_l_fade) : (0.0)) + ((((double)((((double)((v_l_prev) == (4.0)))) && (((double)((v_l_cur) != (4.0))))))) != 0.0 ? ((1.0 - v_l_fade)) : (0.0)));
    v_l_adi = ((((double)((((double)((v_l_run) > (0.5)))) && (((double)((((double)((v_l_cur) == (5.0)))) || (((double)((((double)((v_l_prev) == (5.0)))) && (((double)((v_l_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_l_mdi = (((((double)((v_l_cur) == (5.0)))) != 0.0 ? (v_l_fade) : (0.0)) + ((((double)((((double)((v_l_prev) == (5.0)))) && (((double)((v_l_cur) != (5.0))))))) != 0.0 ? ((1.0 - v_l_fade)) : (0.0)));
    v_l_sh_g = v_l_gw;
    v_l_sh_R1 = (0.3 + ((0.7 * (1.0 - v_l_rz)) * (1.0 - v_l_rz)));
    v_l_sh_R = (((0.8 * (1.0 - v_l_rz)) * (1.0 - v_l_rz)) - (0.08 * pow(v_l_rz, 30.0)));
    v_l_sh_fb = (0.92 * v_l_chr);
    v_l_k3_g = v_l_gw;
    v_l_k3_K = (0.05 + (2.03 * pow(v_l_rz, 1.1)));
    v_l_k3_L = (4.0 * exp2(((-4.0) * v_l_chr)));
    v_l_ld_g = v_l_gw;
    v_l_ld_k = (4.3 * pow(v_l_rz, 1.3));
    v_l_ld_bc = (v_l_cmp * 1.0);
    v_l_ld_hs = (1.0 + (2.0 * v_l_chr));
    v_l_st_g = v_l_gw;
    v_l_st_K = (1.0 + (2.1 * pow(v_l_rz, 1.3)));
    v_l_st_kd = (1.0 / pow(v_l_st_K, v_l_cmp));
    v_l_se_g = v_l_gw;
    v_l_se_R = pow(20.0, (-v_l_rz));
    v_l_di_k = (19.549999999999997 * pow(v_l_rz, 1.8));
    v_l_di_g = (v_l_gw / (0.1494 + (1.2648 * sqrt(fmin((v_l_di_k / 17.0), 1.06)))));
    v_l_di_gf = tan(((M_PI * fmin((8.0 * exp2((5.2 * v_l_chr))), (0.45 * v_fso))) / v_fso));
    v_l_di_Gf = (v_l_di_gf / (1.0 + v_l_di_gf));
    if ((((double)((v_l_ash) < (0.5)))) != 0.0) {
        v_l_L_sh_s1a = 0.0;
        v_l_L_sh_s2a = 0.0;
        v_l_L_sh_ba = 0.0;
        v_l_L_sh_s1b = 0.0;
        v_l_L_sh_s2b = 0.0;
        v_l_L_sh_bb = 0.0;
        v_l_L_sh_yp = 0.0;
        v_l_R_sh_s1a = 0.0;
        v_l_R_sh_s2a = 0.0;
        v_l_R_sh_ba = 0.0;
        v_l_R_sh_s1b = 0.0;
        v_l_R_sh_s2b = 0.0;
        v_l_R_sh_bb = 0.0;
        v_l_R_sh_yp = 0.0;
    }
    if ((((double)((v_l_ak3) < (0.5)))) != 0.0) {
        v_l_L_k3_s1 = 0.0;
        v_l_L_k3_s2 = 0.0;
        v_l_L_k3_s3 = 0.0;
        v_l_L_k3_yp = 0.0;
        v_l_R_k3_s1 = 0.0;
        v_l_R_k3_s2 = 0.0;
        v_l_R_k3_s3 = 0.0;
        v_l_R_k3_yp = 0.0;
    }
    if ((((double)((v_l_ald) < (0.5)))) != 0.0) {
        v_l_L_ld_s1 = 0.0;
        v_l_L_ld_s2 = 0.0;
        v_l_L_ld_s3 = 0.0;
        v_l_L_ld_s4 = 0.0;
        v_l_L_ld_p0 = 0.0;
        v_l_L_ld_p1 = 0.0;
        v_l_L_ld_p2 = 0.0;
        v_l_L_ld_p3 = 0.0;
        v_l_L_ld_p4 = 0.0;
        v_l_R_ld_s1 = 0.0;
        v_l_R_ld_s2 = 0.0;
        v_l_R_ld_s3 = 0.0;
        v_l_R_ld_s4 = 0.0;
        v_l_R_ld_p0 = 0.0;
        v_l_R_ld_p1 = 0.0;
        v_l_R_ld_p2 = 0.0;
        v_l_R_ld_p3 = 0.0;
        v_l_R_ld_p4 = 0.0;
    }
    if ((((double)((v_l_ast) < (0.5)))) != 0.0) {
        v_l_L_st_s1 = 0.0;
        v_l_L_st_s2 = 0.0;
        v_l_L_st_d1 = 0.0;
        v_l_L_st_d2 = 0.0;
        v_l_L_st_vb = 0.0;
        v_l_R_st_s1 = 0.0;
        v_l_R_st_s2 = 0.0;
        v_l_R_st_d1 = 0.0;
        v_l_R_st_d2 = 0.0;
        v_l_R_st_vb = 0.0;
    }
    if ((((double)((v_l_ase) < (0.5)))) != 0.0) {
        v_l_L_se_s1 = 0.0;
        v_l_L_se_s2 = 0.0;
        v_l_L_se_hq = 0.0;
        v_l_L_se_bq = 0.0;
        v_l_R_se_s1 = 0.0;
        v_l_R_se_s2 = 0.0;
        v_l_R_se_hq = 0.0;
        v_l_R_se_bq = 0.0;
    }
    if ((((double)((v_l_adi) < (0.5)))) != 0.0) {
        v_l_L_di_s1 = 0.0;
        v_l_L_di_s2 = 0.0;
        v_l_L_di_s3 = 0.0;
        v_l_L_di_s4 = 0.0;
        v_l_L_di_v1 = 0.0;
        v_l_L_di_v2 = 0.0;
        v_l_L_di_v3 = 0.0;
        v_l_L_di_v4 = 0.0;
        v_l_L_di_sf = 0.0;
        v_l_L_di_sc = 0.0;
        v_l_R_di_s1 = 0.0;
        v_l_R_di_s2 = 0.0;
        v_l_R_di_s3 = 0.0;
        v_l_R_di_s4 = 0.0;
        v_l_R_di_v1 = 0.0;
        v_l_R_di_v2 = 0.0;
        v_l_R_di_v3 = 0.0;
        v_l_R_di_v4 = 0.0;
        v_l_R_di_sf = 0.0;
        v_l_R_di_sc = 0.0;
    }
    if ((((double)((((double)((v_l_xa) < (0.5)))) || (((double)((v_l_run) < (0.5))))))) != 0.0) {
        v_l_L_x0_s1 = 0.0;
        v_l_L_x0_s2 = 0.0;
        v_l_R_x0_s1 = 0.0;
        v_l_R_x0_s2 = 0.0;
    }
    if ((((double)((((double)((v_l_xb) < (0.5)))) || (((double)((v_l_run) < (0.5))))))) != 0.0) {
        v_l_L_x1_s1 = 0.0;
        v_l_L_x1_s2 = 0.0;
        v_l_R_x1_s1 = 0.0;
        v_l_R_x1_s2 = 0.0;
    }
    if ((((double)((((double)((v_l_xc) < (0.5)))) || (((double)((v_l_run) < (0.5))))))) != 0.0) {
        v_l_L_x2_s1 = 0.0;
        v_l_L_x2_s2 = 0.0;
        v_l_R_x2_s1 = 0.0;
        v_l_R_x2_s2 = 0.0;
    }
    v_h_lc = (Hs_H_h_lc + (v_a_cut * (log2(gclamp(P_h_cut, 20.0, 2000.0)) - Hs_H_h_lc)));
    v_h_rz = (Hs_H_h_rz + (v_a_par * ((gclamp(P_h_res, 0.0, 100.0) * 0.01) - Hs_H_h_rz)));
    v_h_drv = (Hs_H_h_drv + (v_a_par * ((gclamp(P_h_drive, 0.0, 100.0) * 0.01) - Hs_H_h_drv)));
    v_h_cmp = (Hs_H_h_cmp + (v_a_par * ((gclamp(P_h_comp, 0.0, 100.0) * 0.01) - Hs_H_h_cmp)));
    v_h_chr = (Hs_H_h_chr + (v_a_par * ((gclamp(P_h_char, 0.0, 100.0) * 0.01) - Hs_H_h_chr)));
    v_h_fc = exp2(v_h_lc);
    v_h_fcc = fmin(v_h_fc, (0.45 * v_fso));
    v_h_gw = tan(((M_PI * v_h_fcc) / v_fso));
    v_h_ent = ((((double)((P_h_on) > (0.5)))) != 0.0 ? (1.0) : (0.0));
    v_h_en = (Hs_H_h_en + (v_a_mix * (v_h_ent - Hs_H_h_en)));
    if ((((double)((((double)((v_h_ent) < (0.5)))) && (((double)((v_h_en) < (0.0001))))))) != 0.0) {
        v_h_en = 0.0;
    }
    if ((((double)((((double)((v_h_ent) > (0.5)))) && (((double)((v_h_en) > (0.9999))))))) != 0.0) {
        v_h_en = 1.0;
    }
    v_h_det = gclamp(((v_h_fc - 20.0) * 0.2), 0.0, 1.0);
    v_h_wet = (v_h_en * v_h_det);
    v_h_run = ((((double)((v_h_wet) > (0.0)))) != 0.0 ? (1.0) : (0.0));
    v_h_d = (0.25 * exp2((5.0 * v_h_drv)));
    v_h_id = (1.0 / v_h_d);
    v_h_osc = (v_h_id * exp2(((5.0 * v_h_drv) * (1.0 - (0.5 * v_h_cmp)))));
    v_h_msel = gclamp(floor((P_h_model + 0.5)), 0.0, 4.0);
    v_h_cur = Hs_H_h_cur;
    v_h_prev = Hs_H_h_prev;
    v_h_fade = Hs_H_h_fade;
    if ((((double)((v_h_msel) != (v_h_cur)))) != 0.0) {
        v_h_prev = v_h_cur;
        v_h_cur = v_h_msel;
        v_h_fade = 0.0;
    }
    v_h_fade = fmin(1.0, (v_h_fade + v_fstep));
    v_h_ssel = gclamp(floor((P_h_slope + 0.5)), 0.0, 3.0);
    v_h_tit = ((((double)((v_h_ssel) > (0.5)))) != 0.0 ? (1.0) : (0.0));
    v_h_n12 = ((((double)((((double)((((double)((v_h_cur) == (1.0)))) || (((double)((v_h_cur) == (3.0))))))) || (((double)((v_h_cur) == (4.0))))))) != 0.0 ? (1.0) : (0.0));
    v_h_next = ((((double)((v_h_n12) > (0.5)))) != 0.0 ? (v_h_ssel) : (fmax(0.0, (v_h_ssel - 1.0))));
    v_h_ti = (Hs_H_h_ti + (v_a_mix * (v_h_tit - Hs_H_h_ti)));
    v_h_w0 = (Hs_H_h_w0 + (v_a_mix * (((((double)((v_h_next) == (0.0)))) != 0.0 ? (1.0) : (0.0)) - Hs_H_h_w0)));
    v_h_w1 = (Hs_H_h_w1 + (v_a_mix * (((((double)((v_h_next) == (1.0)))) != 0.0 ? (1.0) : (0.0)) - Hs_H_h_w1)));
    v_h_w2 = (Hs_H_h_w2 + (v_a_mix * (((((double)((v_h_next) == (2.0)))) != 0.0 ? (1.0) : (0.0)) - Hs_H_h_w2)));
    v_h_w3 = (Hs_H_h_w3 + (v_a_mix * (((((double)((v_h_next) == (3.0)))) != 0.0 ? (1.0) : (0.0)) - Hs_H_h_w3)));
    v_h_xa = ((((double)((((v_h_w1 + v_h_w2) + v_h_w3)) > (0.00001)))) != 0.0 ? (1.0) : (0.0));
    v_h_xb = ((((double)(((v_h_w2 + v_h_w3)) > (0.00001)))) != 0.0 ? (1.0) : (0.0));
    v_h_xc = ((((double)((v_h_w3) > (0.00001)))) != 0.0 ? (1.0) : (0.0));
    v_h_gx = v_h_gw;
    v_h_ash = ((((double)((((double)((v_h_run) > (0.5)))) && (((double)((((double)((v_h_cur) == (0.0)))) || (((double)((((double)((v_h_prev) == (0.0)))) && (((double)((v_h_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_h_msh = (((((double)((v_h_cur) == (0.0)))) != 0.0 ? (v_h_fade) : (0.0)) + ((((double)((((double)((v_h_prev) == (0.0)))) && (((double)((v_h_cur) != (0.0))))))) != 0.0 ? ((1.0 - v_h_fade)) : (0.0)));
    v_h_ak3 = ((((double)((((double)((v_h_run) > (0.5)))) && (((double)((((double)((v_h_cur) == (1.0)))) || (((double)((((double)((v_h_prev) == (1.0)))) && (((double)((v_h_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_h_mk3 = (((((double)((v_h_cur) == (1.0)))) != 0.0 ? (v_h_fade) : (0.0)) + ((((double)((((double)((v_h_prev) == (1.0)))) && (((double)((v_h_cur) != (1.0))))))) != 0.0 ? ((1.0 - v_h_fade)) : (0.0)));
    v_h_ald = ((((double)((((double)((v_h_run) > (0.5)))) && (((double)((((double)((v_h_cur) == (2.0)))) || (((double)((((double)((v_h_prev) == (2.0)))) && (((double)((v_h_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_h_mld = (((((double)((v_h_cur) == (2.0)))) != 0.0 ? (v_h_fade) : (0.0)) + ((((double)((((double)((v_h_prev) == (2.0)))) && (((double)((v_h_cur) != (2.0))))))) != 0.0 ? ((1.0 - v_h_fade)) : (0.0)));
    v_h_ast = ((((double)((((double)((v_h_run) > (0.5)))) && (((double)((((double)((v_h_cur) == (3.0)))) || (((double)((((double)((v_h_prev) == (3.0)))) && (((double)((v_h_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_h_mst = (((((double)((v_h_cur) == (3.0)))) != 0.0 ? (v_h_fade) : (0.0)) + ((((double)((((double)((v_h_prev) == (3.0)))) && (((double)((v_h_cur) != (3.0))))))) != 0.0 ? ((1.0 - v_h_fade)) : (0.0)));
    v_h_ase = ((((double)((((double)((v_h_run) > (0.5)))) && (((double)((((double)((v_h_cur) == (4.0)))) || (((double)((((double)((v_h_prev) == (4.0)))) && (((double)((v_h_fade) < (1.0))))))))))))) != 0.0 ? (1.0) : (0.0));
    v_h_mse = (((((double)((v_h_cur) == (4.0)))) != 0.0 ? (v_h_fade) : (0.0)) + ((((double)((((double)((v_h_prev) == (4.0)))) && (((double)((v_h_cur) != (4.0))))))) != 0.0 ? ((1.0 - v_h_fade)) : (0.0)));
    v_h_sh_g = v_h_gw;
    v_h_sh_R1 = (0.3 + ((0.7 * (1.0 - v_h_rz)) * (1.0 - v_h_rz)));
    v_h_sh_R = (((0.8 * (1.0 - v_h_rz)) * (1.0 - v_h_rz)) - (0.08 * pow(v_h_rz, 30.0)));
    v_h_sh_fb = (0.92 * v_h_chr);
    v_h_k3_g = v_h_gw;
    v_h_k3_K = (0.05 + (2.03 * pow(v_h_rz, 1.1)));
    v_h_k3_L = (4.0 * exp2(((-4.0) * v_h_chr)));
    v_h_ld_g = v_h_gw;
    v_h_ld_k = (4.3 * pow(v_h_rz, 1.3));
    v_h_ld_bc = (v_h_cmp * 0.0);
    v_h_ld_hs = (1.0 + (2.0 * v_h_chr));
    v_h_st_g = v_h_gw;
    v_h_st_K = (1.0 + (2.1 * pow(v_h_rz, 1.3)));
    v_h_st_kd = (1.0 / pow(v_h_st_K, v_h_cmp));
    v_h_se_g = v_h_gw;
    v_h_se_R = pow(20.0, (-v_h_rz));
    if ((((double)((v_h_ash) < (0.5)))) != 0.0) {
        v_h_L_sh_s1a = 0.0;
        v_h_L_sh_s2a = 0.0;
        v_h_L_sh_ba = 0.0;
        v_h_L_sh_s1b = 0.0;
        v_h_L_sh_s2b = 0.0;
        v_h_L_sh_bb = 0.0;
        v_h_L_sh_yp = 0.0;
        v_h_R_sh_s1a = 0.0;
        v_h_R_sh_s2a = 0.0;
        v_h_R_sh_ba = 0.0;
        v_h_R_sh_s1b = 0.0;
        v_h_R_sh_s2b = 0.0;
        v_h_R_sh_bb = 0.0;
        v_h_R_sh_yp = 0.0;
    }
    if ((((double)((v_h_ak3) < (0.5)))) != 0.0) {
        v_h_L_k3_s1 = 0.0;
        v_h_L_k3_s2 = 0.0;
        v_h_L_k3_s3 = 0.0;
        v_h_L_k3_yp = 0.0;
        v_h_R_k3_s1 = 0.0;
        v_h_R_k3_s2 = 0.0;
        v_h_R_k3_s3 = 0.0;
        v_h_R_k3_yp = 0.0;
    }
    if ((((double)((v_h_ald) < (0.5)))) != 0.0) {
        v_h_L_ld_s1 = 0.0;
        v_h_L_ld_s2 = 0.0;
        v_h_L_ld_s3 = 0.0;
        v_h_L_ld_s4 = 0.0;
        v_h_L_ld_p0 = 0.0;
        v_h_L_ld_p1 = 0.0;
        v_h_L_ld_p2 = 0.0;
        v_h_L_ld_p3 = 0.0;
        v_h_L_ld_p4 = 0.0;
        v_h_R_ld_s1 = 0.0;
        v_h_R_ld_s2 = 0.0;
        v_h_R_ld_s3 = 0.0;
        v_h_R_ld_s4 = 0.0;
        v_h_R_ld_p0 = 0.0;
        v_h_R_ld_p1 = 0.0;
        v_h_R_ld_p2 = 0.0;
        v_h_R_ld_p3 = 0.0;
        v_h_R_ld_p4 = 0.0;
    }
    if ((((double)((v_h_ast) < (0.5)))) != 0.0) {
        v_h_L_st_s1 = 0.0;
        v_h_L_st_s2 = 0.0;
        v_h_L_st_d1 = 0.0;
        v_h_L_st_d2 = 0.0;
        v_h_L_st_vb = 0.0;
        v_h_R_st_s1 = 0.0;
        v_h_R_st_s2 = 0.0;
        v_h_R_st_d1 = 0.0;
        v_h_R_st_d2 = 0.0;
        v_h_R_st_vb = 0.0;
    }
    if ((((double)((v_h_ase) < (0.5)))) != 0.0) {
        v_h_L_se_s1 = 0.0;
        v_h_L_se_s2 = 0.0;
        v_h_L_se_hq = 0.0;
        v_h_L_se_bq = 0.0;
        v_h_R_se_s1 = 0.0;
        v_h_R_se_s2 = 0.0;
        v_h_R_se_hq = 0.0;
        v_h_R_se_bq = 0.0;
    }
    if ((((double)((((double)((v_h_xa) < (0.5)))) || (((double)((v_h_run) < (0.5))))))) != 0.0) {
        v_h_L_x0_s1 = 0.0;
        v_h_L_x0_s2 = 0.0;
        v_h_R_x0_s1 = 0.0;
        v_h_R_x0_s2 = 0.0;
    }
    if ((((double)((((double)((v_h_xb) < (0.5)))) || (((double)((v_h_run) < (0.5))))))) != 0.0) {
        v_h_L_x1_s1 = 0.0;
        v_h_L_x1_s2 = 0.0;
        v_h_R_x1_s1 = 0.0;
        v_h_R_x1_s2 = 0.0;
    }
    if ((((double)((((double)((v_h_xc) < (0.5)))) || (((double)((v_h_run) < (0.5))))))) != 0.0) {
        v_h_L_x2_s1 = 0.0;
        v_h_L_x2_s2 = 0.0;
        v_h_R_x2_s1 = 0.0;
        v_h_R_x2_s2 = 0.0;
    }
    v_cfg_o = ((((double)((P_order_sel) > (0.5)))) != 0.0 ? (1.0) : (0.0));
    v_cfg_s = ((((double)((P_ovs_sel) > (0.5)))) != 0.0 ? (1.0) : (0.0));
    v_pend = ((((double)((((double)((v_cfg_o) != (v_cur_order)))) || (((double)((v_cfg_s) != (v_cur_os))))))) != 0.0 ? (1.0) : (0.0));
    v_duck = Hs_H_duck;
    v_duck = ((((double)((v_pend) > (0.5)))) != 0.0 ? (fmax(0.0, (v_duck - v_dstep))) : (fmin(1.0, (v_duck + v_dstep))));
    v_new_order = v_cur_order;
    v_new_os = v_cur_os;
    v_rst = 0.0;
    if ((((double)((((double)((v_pend) > (0.5)))) && (((double)((v_duck) <= (0.0))))))) != 0.0) {
        v_new_order = v_cfg_o;
        v_new_os = v_cfg_s;
        v_rst = ((((double)((v_cfg_s) != (v_cur_os)))) != 0.0 ? (1.0) : (0.0));
    }
    v_xa_L = v_x_L;
    v_xb_L = 0.0;
    v_xa_R = v_x_R;
    v_xb_R = 0.0;
    if ((((double)((v_ovs) > (1.5)))) != 0.0) {
        { double _t0, _t1, _t2, _t3, _t4, _t5, _t6; F_f_ap5(v_x_L, v_os_L_upa0, v_os_L_upa1, v_os_L_upa2, v_os_L_upa3, v_os_L_upa4, v_os_L_upa5, 0.035979631179546, 0.270744078039831, 0.557994617257913, 0.775098715397111, 0.916958938825425, &_t0, &_t1, &_t2, &_t3, &_t4, &_t5, &_t6);
          v_xa_L = _t0;
          v_os_L_upa0 = _t1;
          v_os_L_upa1 = _t2;
          v_os_L_upa2 = _t3;
          v_os_L_upa3 = _t4;
          v_os_L_upa4 = _t5;
          v_os_L_upa5 = _t6;
        }
        { double _t7, _t8, _t9, _t10, _t11, _t12, _t13; F_f_ap5(v_x_L, v_os_L_upb0, v_os_L_upb1, v_os_L_upb2, v_os_L_upb3, v_os_L_upb4, v_os_L_upb5, 0.134200951194299, 0.418804850254691, 0.677594451212584, 0.853151529122229, 0.972847950939362, &_t7, &_t8, &_t9, &_t10, &_t11, &_t12, &_t13);
          v_xb_L = _t7;
          v_os_L_upb0 = _t8;
          v_os_L_upb1 = _t9;
          v_os_L_upb2 = _t10;
          v_os_L_upb3 = _t11;
          v_os_L_upb4 = _t12;
          v_os_L_upb5 = _t13;
        }
        { double _t14, _t15, _t16, _t17, _t18, _t19, _t20; F_f_ap5(v_x_R, v_os_R_upa0, v_os_R_upa1, v_os_R_upa2, v_os_R_upa3, v_os_R_upa4, v_os_R_upa5, 0.035979631179546, 0.270744078039831, 0.557994617257913, 0.775098715397111, 0.916958938825425, &_t14, &_t15, &_t16, &_t17, &_t18, &_t19, &_t20);
          v_xa_R = _t14;
          v_os_R_upa0 = _t15;
          v_os_R_upa1 = _t16;
          v_os_R_upa2 = _t17;
          v_os_R_upa3 = _t18;
          v_os_R_upa4 = _t19;
          v_os_R_upa5 = _t20;
        }
        { double _t21, _t22, _t23, _t24, _t25, _t26, _t27; F_f_ap5(v_x_R, v_os_R_upb0, v_os_R_upb1, v_os_R_upb2, v_os_R_upb3, v_os_R_upb4, v_os_R_upb5, 0.134200951194299, 0.418804850254691, 0.677594451212584, 0.853151529122229, 0.972847950939362, &_t21, &_t22, &_t23, &_t24, &_t25, &_t26, &_t27);
          v_xb_R = _t21;
          v_os_R_upb0 = _t22;
          v_os_R_upb1 = _t23;
          v_os_R_upb2 = _t24;
          v_os_R_upb3 = _t25;
          v_os_R_upb4 = _t26;
          v_os_R_upb5 = _t27;
        }
    }
    v_zb_L = 0.0;
    v_zb_R = 0.0;
    v_hya_L = 0.0;
    v_hya_R = 0.0;
    if ((((double)((v_cur_order) > (0.5)))) != 0.0) {
        v_hya_L = v_xa_L;
        v_hya_R = v_xa_R;
        if ((((double)((v_h_run) > (0.5)))) != 0.0) {
            v_hi_L = (v_xa_L * v_h_d);
            v_hb_L = 0.0;
            if ((((double)((v_h_ash) > (0.5)))) != 0.0) {
                { double _t28, _t29, _t30, _t31, _t32, _t33, _t34, _t35, _t36; F_f_sherman(v_hi_L, v_h_L_sh_s1a, v_h_L_sh_s2a, v_h_L_sh_ba, v_h_L_sh_s1b, v_h_L_sh_s2b, v_h_L_sh_bb, v_h_L_sh_yp, v_h_sh_g, v_h_sh_R1, v_h_sh_R, v_h_sh_fb, v_h_ti, 1.0, &_t28, &_t29, &_t30, &_t31, &_t32, &_t33, &_t34, &_t35, &_t36);
                  v_o12 = _t28;
                  v_o24 = _t29;
                  v_h_L_sh_s1a = _t30;
                  v_h_L_sh_s2a = _t31;
                  v_h_L_sh_ba = _t32;
                  v_h_L_sh_s1b = _t33;
                  v_h_L_sh_s2b = _t34;
                  v_h_L_sh_bb = _t35;
                  v_h_L_sh_yp = _t36;
                }
                v_hb_L = (v_hb_L + (v_h_msh * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_h_ak3) > (0.5)))) != 0.0) {
                { double _t37, _t38, _t39, _t40, _t41; F_f_k35hp(v_hi_L, v_h_L_k3_s1, v_h_L_k3_s2, v_h_L_k3_s3, v_h_L_k3_yp, v_h_k3_g, v_h_k3_K, v_h_k3_L, &_t37, &_t38, &_t39, &_t40, &_t41);
                  v_o1 = _t37;
                  v_h_L_k3_s1 = _t38;
                  v_h_L_k3_s2 = _t39;
                  v_h_L_k3_s3 = _t40;
                  v_h_L_k3_yp = _t41;
                }
                v_hb_L = (v_hb_L + (v_h_mk3 * v_o1));
            }
            if ((((double)((v_h_ald) > (0.5)))) != 0.0) {
                { double _t42, _t43, _t44, _t45, _t46, _t47, _t48, _t49, _t50, _t51, _t52; F_f_ladder(v_hi_L, v_h_L_ld_s1, v_h_L_ld_s2, v_h_L_ld_s3, v_h_L_ld_s4, v_h_L_ld_p0, v_h_L_ld_p1, v_h_L_ld_p2, v_h_L_ld_p3, v_h_L_ld_p4, v_h_ld_g, v_h_ld_k, v_h_ld_bc, v_h_ld_hs, 1.0, &_t42, &_t43, &_t44, &_t45, &_t46, &_t47, &_t48, &_t49, &_t50, &_t51, &_t52);
                  v_o12 = _t42;
                  v_o24 = _t43;
                  v_h_L_ld_s1 = _t44;
                  v_h_L_ld_s2 = _t45;
                  v_h_L_ld_s3 = _t46;
                  v_h_L_ld_s4 = _t47;
                  v_h_L_ld_p0 = _t48;
                  v_h_L_ld_p1 = _t49;
                  v_h_L_ld_p2 = _t50;
                  v_h_L_ld_p3 = _t51;
                  v_h_L_ld_p4 = _t52;
                }
                v_hb_L = (v_hb_L + (v_h_mld * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_h_ast) > (0.5)))) != 0.0) {
                { double _t53, _t54, _t55, _t56, _t57, _t58; F_f_steiner(((v_hi_L * (1.0 - v_h_chr)) * 0.0), (v_hi_L * v_h_chr), ((v_hi_L * (1.0 - v_h_chr)) * 1.0), v_h_L_st_s1, v_h_L_st_s2, v_h_L_st_d1, v_h_L_st_d2, v_h_L_st_vb, v_h_st_g, v_h_st_K, &_t53, &_t54, &_t55, &_t56, &_t57, &_t58);
                  v_o1 = _t53;
                  v_h_L_st_s1 = _t54;
                  v_h_L_st_s2 = _t55;
                  v_h_L_st_d1 = _t56;
                  v_h_L_st_d2 = _t57;
                  v_h_L_st_vb = _t58;
                }
                v_hb_L = (v_hb_L + ((v_h_mst * v_o1) * v_h_st_kd));
            }
            if ((((double)((v_h_ase) > (0.5)))) != 0.0) {
                { double _t59, _t60, _t61, _t62, _t63; F_f_sem(v_hi_L, v_h_L_se_s1, v_h_L_se_s2, v_h_L_se_hq, v_h_L_se_bq, v_h_se_g, v_h_se_R, v_h_chr, 1.0, &_t59, &_t60, &_t61, &_t62, &_t63);
                  v_o1 = _t59;
                  v_h_L_se_s1 = _t60;
                  v_h_L_se_s2 = _t61;
                  v_h_L_se_hq = _t62;
                  v_h_L_se_bq = _t63;
                }
                v_hb_L = (v_hb_L + (v_h_mse * v_o1));
            }
            v_e0 = v_hb_L;
            v_e1 = 0.0;
            v_e2 = 0.0;
            v_e3 = 0.0;
            if ((((double)((v_h_xa) > (0.5)))) != 0.0) {
                { double _t64, _t65, _t66, _t67, _t68; F_f_svf(v_e0, v_h_L_x0_s1, v_h_L_x0_s2, v_h_gx, 0.7071067811865476, &_t64, &_t65, &_t66, &_t67, &_t68);
                  v_eh = _t64;
                  v_eb = _t65;
                  v_el = _t66;
                  v_h_L_x0_s1 = _t67;
                  v_h_L_x0_s2 = _t68;
                }
                v_h_L_x0_s1 = fixdenorm(v_h_L_x0_s1);
                v_h_L_x0_s2 = fixdenorm(v_h_L_x0_s2);
                v_e1 = v_eh;
            }
            if ((((double)((v_h_xb) > (0.5)))) != 0.0) {
                { double _t69, _t70, _t71, _t72, _t73; F_f_svf(v_e1, v_h_L_x1_s1, v_h_L_x1_s2, v_h_gx, 0.7071067811865476, &_t69, &_t70, &_t71, &_t72, &_t73);
                  v_eh = _t69;
                  v_eb = _t70;
                  v_el = _t71;
                  v_h_L_x1_s1 = _t72;
                  v_h_L_x1_s2 = _t73;
                }
                v_h_L_x1_s1 = fixdenorm(v_h_L_x1_s1);
                v_h_L_x1_s2 = fixdenorm(v_h_L_x1_s2);
                v_e2 = v_eh;
            }
            if ((((double)((v_h_xc) > (0.5)))) != 0.0) {
                { double _t74, _t75, _t76, _t77, _t78; F_f_svf(v_e2, v_h_L_x2_s1, v_h_L_x2_s2, v_h_gx, 0.7071067811865476, &_t74, &_t75, &_t76, &_t77, &_t78);
                  v_eh = _t74;
                  v_eb = _t75;
                  v_el = _t76;
                  v_h_L_x2_s1 = _t77;
                  v_h_L_x2_s2 = _t78;
                }
                v_h_L_x2_s1 = fixdenorm(v_h_L_x2_s1);
                v_h_L_x2_s2 = fixdenorm(v_h_L_x2_s2);
                v_e3 = v_eh;
            }
            v_wet_L = (((((v_h_w0 * v_e0) + (v_h_w1 * v_e1)) + (v_h_w2 * v_e2)) + (v_h_w3 * v_e3)) * v_h_osc);
            v_hya_L = (v_xa_L + (v_h_wet * (v_wet_L - v_xa_L)));
            v_hi_R = (v_xa_R * v_h_d);
            v_hb_R = 0.0;
            if ((((double)((v_h_ash) > (0.5)))) != 0.0) {
                { double _t79, _t80, _t81, _t82, _t83, _t84, _t85, _t86, _t87; F_f_sherman(v_hi_R, v_h_R_sh_s1a, v_h_R_sh_s2a, v_h_R_sh_ba, v_h_R_sh_s1b, v_h_R_sh_s2b, v_h_R_sh_bb, v_h_R_sh_yp, v_h_sh_g, v_h_sh_R1, v_h_sh_R, v_h_sh_fb, v_h_ti, 1.0, &_t79, &_t80, &_t81, &_t82, &_t83, &_t84, &_t85, &_t86, &_t87);
                  v_o12 = _t79;
                  v_o24 = _t80;
                  v_h_R_sh_s1a = _t81;
                  v_h_R_sh_s2a = _t82;
                  v_h_R_sh_ba = _t83;
                  v_h_R_sh_s1b = _t84;
                  v_h_R_sh_s2b = _t85;
                  v_h_R_sh_bb = _t86;
                  v_h_R_sh_yp = _t87;
                }
                v_hb_R = (v_hb_R + (v_h_msh * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_h_ak3) > (0.5)))) != 0.0) {
                { double _t88, _t89, _t90, _t91, _t92; F_f_k35hp(v_hi_R, v_h_R_k3_s1, v_h_R_k3_s2, v_h_R_k3_s3, v_h_R_k3_yp, v_h_k3_g, v_h_k3_K, v_h_k3_L, &_t88, &_t89, &_t90, &_t91, &_t92);
                  v_o1 = _t88;
                  v_h_R_k3_s1 = _t89;
                  v_h_R_k3_s2 = _t90;
                  v_h_R_k3_s3 = _t91;
                  v_h_R_k3_yp = _t92;
                }
                v_hb_R = (v_hb_R + (v_h_mk3 * v_o1));
            }
            if ((((double)((v_h_ald) > (0.5)))) != 0.0) {
                { double _t93, _t94, _t95, _t96, _t97, _t98, _t99, _t100, _t101, _t102, _t103; F_f_ladder(v_hi_R, v_h_R_ld_s1, v_h_R_ld_s2, v_h_R_ld_s3, v_h_R_ld_s4, v_h_R_ld_p0, v_h_R_ld_p1, v_h_R_ld_p2, v_h_R_ld_p3, v_h_R_ld_p4, v_h_ld_g, v_h_ld_k, v_h_ld_bc, v_h_ld_hs, 1.0, &_t93, &_t94, &_t95, &_t96, &_t97, &_t98, &_t99, &_t100, &_t101, &_t102, &_t103);
                  v_o12 = _t93;
                  v_o24 = _t94;
                  v_h_R_ld_s1 = _t95;
                  v_h_R_ld_s2 = _t96;
                  v_h_R_ld_s3 = _t97;
                  v_h_R_ld_s4 = _t98;
                  v_h_R_ld_p0 = _t99;
                  v_h_R_ld_p1 = _t100;
                  v_h_R_ld_p2 = _t101;
                  v_h_R_ld_p3 = _t102;
                  v_h_R_ld_p4 = _t103;
                }
                v_hb_R = (v_hb_R + (v_h_mld * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_h_ast) > (0.5)))) != 0.0) {
                { double _t104, _t105, _t106, _t107, _t108, _t109; F_f_steiner(((v_hi_R * (1.0 - v_h_chr)) * 0.0), (v_hi_R * v_h_chr), ((v_hi_R * (1.0 - v_h_chr)) * 1.0), v_h_R_st_s1, v_h_R_st_s2, v_h_R_st_d1, v_h_R_st_d2, v_h_R_st_vb, v_h_st_g, v_h_st_K, &_t104, &_t105, &_t106, &_t107, &_t108, &_t109);
                  v_o1 = _t104;
                  v_h_R_st_s1 = _t105;
                  v_h_R_st_s2 = _t106;
                  v_h_R_st_d1 = _t107;
                  v_h_R_st_d2 = _t108;
                  v_h_R_st_vb = _t109;
                }
                v_hb_R = (v_hb_R + ((v_h_mst * v_o1) * v_h_st_kd));
            }
            if ((((double)((v_h_ase) > (0.5)))) != 0.0) {
                { double _t110, _t111, _t112, _t113, _t114; F_f_sem(v_hi_R, v_h_R_se_s1, v_h_R_se_s2, v_h_R_se_hq, v_h_R_se_bq, v_h_se_g, v_h_se_R, v_h_chr, 1.0, &_t110, &_t111, &_t112, &_t113, &_t114);
                  v_o1 = _t110;
                  v_h_R_se_s1 = _t111;
                  v_h_R_se_s2 = _t112;
                  v_h_R_se_hq = _t113;
                  v_h_R_se_bq = _t114;
                }
                v_hb_R = (v_hb_R + (v_h_mse * v_o1));
            }
            v_e0 = v_hb_R;
            v_e1 = 0.0;
            v_e2 = 0.0;
            v_e3 = 0.0;
            if ((((double)((v_h_xa) > (0.5)))) != 0.0) {
                { double _t115, _t116, _t117, _t118, _t119; F_f_svf(v_e0, v_h_R_x0_s1, v_h_R_x0_s2, v_h_gx, 0.7071067811865476, &_t115, &_t116, &_t117, &_t118, &_t119);
                  v_eh = _t115;
                  v_eb = _t116;
                  v_el = _t117;
                  v_h_R_x0_s1 = _t118;
                  v_h_R_x0_s2 = _t119;
                }
                v_h_R_x0_s1 = fixdenorm(v_h_R_x0_s1);
                v_h_R_x0_s2 = fixdenorm(v_h_R_x0_s2);
                v_e1 = v_eh;
            }
            if ((((double)((v_h_xb) > (0.5)))) != 0.0) {
                { double _t120, _t121, _t122, _t123, _t124; F_f_svf(v_e1, v_h_R_x1_s1, v_h_R_x1_s2, v_h_gx, 0.7071067811865476, &_t120, &_t121, &_t122, &_t123, &_t124);
                  v_eh = _t120;
                  v_eb = _t121;
                  v_el = _t122;
                  v_h_R_x1_s1 = _t123;
                  v_h_R_x1_s2 = _t124;
                }
                v_h_R_x1_s1 = fixdenorm(v_h_R_x1_s1);
                v_h_R_x1_s2 = fixdenorm(v_h_R_x1_s2);
                v_e2 = v_eh;
            }
            if ((((double)((v_h_xc) > (0.5)))) != 0.0) {
                { double _t125, _t126, _t127, _t128, _t129; F_f_svf(v_e2, v_h_R_x2_s1, v_h_R_x2_s2, v_h_gx, 0.7071067811865476, &_t125, &_t126, &_t127, &_t128, &_t129);
                  v_eh = _t125;
                  v_eb = _t126;
                  v_el = _t127;
                  v_h_R_x2_s1 = _t128;
                  v_h_R_x2_s2 = _t129;
                }
                v_h_R_x2_s1 = fixdenorm(v_h_R_x2_s1);
                v_h_R_x2_s2 = fixdenorm(v_h_R_x2_s2);
                v_e3 = v_eh;
            }
            v_wet_R = (((((v_h_w0 * v_e0) + (v_h_w1 * v_e1)) + (v_h_w2 * v_e2)) + (v_h_w3 * v_e3)) * v_h_osc);
            v_hya_R = (v_xa_R + (v_h_wet * (v_wet_R - v_xa_R)));
        }
    }
    v_lsrc_L = ((((double)((v_cur_order) > (0.5)))) != 0.0 ? (v_hya_L) : (v_xa_L));
    v_lsrc_R = ((((double)((v_cur_order) > (0.5)))) != 0.0 ? (v_hya_R) : (v_xa_R));
    v_lya_L = v_lsrc_L;
    v_lya_R = v_lsrc_R;
    if ((((double)((v_l_run) > (0.5)))) != 0.0) {
        v_li_L = (v_lsrc_L * v_l_d);
        v_lb_L = 0.0;
        if ((((double)((v_l_ash) > (0.5)))) != 0.0) {
            { double _t130, _t131, _t132, _t133, _t134, _t135, _t136, _t137, _t138; F_f_sherman(v_li_L, v_l_L_sh_s1a, v_l_L_sh_s2a, v_l_L_sh_ba, v_l_L_sh_s1b, v_l_L_sh_s2b, v_l_L_sh_bb, v_l_L_sh_yp, v_l_sh_g, v_l_sh_R1, v_l_sh_R, v_l_sh_fb, v_l_ti, 0.0, &_t130, &_t131, &_t132, &_t133, &_t134, &_t135, &_t136, &_t137, &_t138);
              v_o12 = _t130;
              v_o24 = _t131;
              v_l_L_sh_s1a = _t132;
              v_l_L_sh_s2a = _t133;
              v_l_L_sh_ba = _t134;
              v_l_L_sh_s1b = _t135;
              v_l_L_sh_s2b = _t136;
              v_l_L_sh_bb = _t137;
              v_l_L_sh_yp = _t138;
            }
            v_lb_L = (v_lb_L + (v_l_msh * (v_o12 + (v_l_ti * (v_o24 - v_o12)))));
        }
        if ((((double)((v_l_ak3) > (0.5)))) != 0.0) {
            { double _t139, _t140, _t141, _t142, _t143; F_f_k35lp(v_li_L, v_l_L_k3_s1, v_l_L_k3_s2, v_l_L_k3_s3, v_l_L_k3_yp, v_l_k3_g, v_l_k3_K, v_l_k3_L, &_t139, &_t140, &_t141, &_t142, &_t143);
              v_o1 = _t139;
              v_l_L_k3_s1 = _t140;
              v_l_L_k3_s2 = _t141;
              v_l_L_k3_s3 = _t142;
              v_l_L_k3_yp = _t143;
            }
            v_lb_L = (v_lb_L + (v_l_mk3 * v_o1));
        }
        if ((((double)((v_l_ald) > (0.5)))) != 0.0) {
            { double _t144, _t145, _t146, _t147, _t148, _t149, _t150, _t151, _t152, _t153, _t154; F_f_ladder(v_li_L, v_l_L_ld_s1, v_l_L_ld_s2, v_l_L_ld_s3, v_l_L_ld_s4, v_l_L_ld_p0, v_l_L_ld_p1, v_l_L_ld_p2, v_l_L_ld_p3, v_l_L_ld_p4, v_l_ld_g, v_l_ld_k, v_l_ld_bc, v_l_ld_hs, 0.0, &_t144, &_t145, &_t146, &_t147, &_t148, &_t149, &_t150, &_t151, &_t152, &_t153, &_t154);
              v_o12 = _t144;
              v_o24 = _t145;
              v_l_L_ld_s1 = _t146;
              v_l_L_ld_s2 = _t147;
              v_l_L_ld_s3 = _t148;
              v_l_L_ld_s4 = _t149;
              v_l_L_ld_p0 = _t150;
              v_l_L_ld_p1 = _t151;
              v_l_L_ld_p2 = _t152;
              v_l_L_ld_p3 = _t153;
              v_l_L_ld_p4 = _t154;
            }
            v_lb_L = (v_lb_L + (v_l_mld * (v_o12 + (v_l_ti * (v_o24 - v_o12)))));
        }
        if ((((double)((v_l_ast) > (0.5)))) != 0.0) {
            { double _t155, _t156, _t157, _t158, _t159, _t160; F_f_steiner(((v_li_L * (1.0 - v_l_chr)) * 1.0), (v_li_L * v_l_chr), ((v_li_L * (1.0 - v_l_chr)) * 0.0), v_l_L_st_s1, v_l_L_st_s2, v_l_L_st_d1, v_l_L_st_d2, v_l_L_st_vb, v_l_st_g, v_l_st_K, &_t155, &_t156, &_t157, &_t158, &_t159, &_t160);
              v_o1 = _t155;
              v_l_L_st_s1 = _t156;
              v_l_L_st_s2 = _t157;
              v_l_L_st_d1 = _t158;
              v_l_L_st_d2 = _t159;
              v_l_L_st_vb = _t160;
            }
            v_lb_L = (v_lb_L + ((v_l_mst * v_o1) * v_l_st_kd));
        }
        if ((((double)((v_l_ase) > (0.5)))) != 0.0) {
            { double _t161, _t162, _t163, _t164, _t165; F_f_sem(v_li_L, v_l_L_se_s1, v_l_L_se_s2, v_l_L_se_hq, v_l_L_se_bq, v_l_se_g, v_l_se_R, v_l_chr, 0.0, &_t161, &_t162, &_t163, &_t164, &_t165);
              v_o1 = _t161;
              v_l_L_se_s1 = _t162;
              v_l_L_se_s2 = _t163;
              v_l_L_se_hq = _t164;
              v_l_L_se_bq = _t165;
            }
            v_lb_L = (v_lb_L + (v_l_mse * v_o1));
        }
        if ((((double)((v_l_adi) > (0.5)))) != 0.0) {
            { double _t166, _t167, _t168, _t169, _t170, _t171, _t172, _t173, _t174, _t175, _t176; F_f_diode(v_li_L, v_l_L_di_s1, v_l_L_di_s2, v_l_L_di_s3, v_l_L_di_s4, v_l_L_di_v1, v_l_L_di_v2, v_l_L_di_v3, v_l_L_di_v4, v_l_L_di_sf, v_l_L_di_sc, v_l_di_g, v_l_di_k, v_l_di_Gf, v_l_cmp, &_t166, &_t167, &_t168, &_t169, &_t170, &_t171, &_t172, &_t173, &_t174, &_t175, &_t176);
              v_o1 = _t166;
              v_l_L_di_s1 = _t167;
              v_l_L_di_s2 = _t168;
              v_l_L_di_s3 = _t169;
              v_l_L_di_s4 = _t170;
              v_l_L_di_v1 = _t171;
              v_l_L_di_v2 = _t172;
              v_l_L_di_v3 = _t173;
              v_l_L_di_v4 = _t174;
              v_l_L_di_sf = _t175;
              v_l_L_di_sc = _t176;
            }
            v_lb_L = (v_lb_L + (v_l_mdi * v_o1));
        }
        v_e0 = v_lb_L;
        v_e1 = 0.0;
        v_e2 = 0.0;
        v_e3 = 0.0;
        if ((((double)((v_l_xa) > (0.5)))) != 0.0) {
            { double _t177, _t178, _t179, _t180, _t181; F_f_svf(v_e0, v_l_L_x0_s1, v_l_L_x0_s2, v_l_gx, 0.7071067811865476, &_t177, &_t178, &_t179, &_t180, &_t181);
              v_eh = _t177;
              v_eb = _t178;
              v_el = _t179;
              v_l_L_x0_s1 = _t180;
              v_l_L_x0_s2 = _t181;
            }
            v_l_L_x0_s1 = fixdenorm(v_l_L_x0_s1);
            v_l_L_x0_s2 = fixdenorm(v_l_L_x0_s2);
            v_e1 = v_el;
        }
        if ((((double)((v_l_xb) > (0.5)))) != 0.0) {
            { double _t182, _t183, _t184, _t185, _t186; F_f_svf(v_e1, v_l_L_x1_s1, v_l_L_x1_s2, v_l_gx, 0.7071067811865476, &_t182, &_t183, &_t184, &_t185, &_t186);
              v_eh = _t182;
              v_eb = _t183;
              v_el = _t184;
              v_l_L_x1_s1 = _t185;
              v_l_L_x1_s2 = _t186;
            }
            v_l_L_x1_s1 = fixdenorm(v_l_L_x1_s1);
            v_l_L_x1_s2 = fixdenorm(v_l_L_x1_s2);
            v_e2 = v_el;
        }
        if ((((double)((v_l_xc) > (0.5)))) != 0.0) {
            { double _t187, _t188, _t189, _t190, _t191; F_f_svf(v_e2, v_l_L_x2_s1, v_l_L_x2_s2, v_l_gx, 0.7071067811865476, &_t187, &_t188, &_t189, &_t190, &_t191);
              v_eh = _t187;
              v_eb = _t188;
              v_el = _t189;
              v_l_L_x2_s1 = _t190;
              v_l_L_x2_s2 = _t191;
            }
            v_l_L_x2_s1 = fixdenorm(v_l_L_x2_s1);
            v_l_L_x2_s2 = fixdenorm(v_l_L_x2_s2);
            v_e3 = v_el;
        }
        v_wet_L = (((((v_l_w0 * v_e0) + (v_l_w1 * v_e1)) + (v_l_w2 * v_e2)) + (v_l_w3 * v_e3)) * v_l_osc);
        v_lya_L = (v_lsrc_L + (v_l_wet * (v_wet_L - v_lsrc_L)));
        v_li_R = (v_lsrc_R * v_l_d);
        v_lb_R = 0.0;
        if ((((double)((v_l_ash) > (0.5)))) != 0.0) {
            { double _t192, _t193, _t194, _t195, _t196, _t197, _t198, _t199, _t200; F_f_sherman(v_li_R, v_l_R_sh_s1a, v_l_R_sh_s2a, v_l_R_sh_ba, v_l_R_sh_s1b, v_l_R_sh_s2b, v_l_R_sh_bb, v_l_R_sh_yp, v_l_sh_g, v_l_sh_R1, v_l_sh_R, v_l_sh_fb, v_l_ti, 0.0, &_t192, &_t193, &_t194, &_t195, &_t196, &_t197, &_t198, &_t199, &_t200);
              v_o12 = _t192;
              v_o24 = _t193;
              v_l_R_sh_s1a = _t194;
              v_l_R_sh_s2a = _t195;
              v_l_R_sh_ba = _t196;
              v_l_R_sh_s1b = _t197;
              v_l_R_sh_s2b = _t198;
              v_l_R_sh_bb = _t199;
              v_l_R_sh_yp = _t200;
            }
            v_lb_R = (v_lb_R + (v_l_msh * (v_o12 + (v_l_ti * (v_o24 - v_o12)))));
        }
        if ((((double)((v_l_ak3) > (0.5)))) != 0.0) {
            { double _t201, _t202, _t203, _t204, _t205; F_f_k35lp(v_li_R, v_l_R_k3_s1, v_l_R_k3_s2, v_l_R_k3_s3, v_l_R_k3_yp, v_l_k3_g, v_l_k3_K, v_l_k3_L, &_t201, &_t202, &_t203, &_t204, &_t205);
              v_o1 = _t201;
              v_l_R_k3_s1 = _t202;
              v_l_R_k3_s2 = _t203;
              v_l_R_k3_s3 = _t204;
              v_l_R_k3_yp = _t205;
            }
            v_lb_R = (v_lb_R + (v_l_mk3 * v_o1));
        }
        if ((((double)((v_l_ald) > (0.5)))) != 0.0) {
            { double _t206, _t207, _t208, _t209, _t210, _t211, _t212, _t213, _t214, _t215, _t216; F_f_ladder(v_li_R, v_l_R_ld_s1, v_l_R_ld_s2, v_l_R_ld_s3, v_l_R_ld_s4, v_l_R_ld_p0, v_l_R_ld_p1, v_l_R_ld_p2, v_l_R_ld_p3, v_l_R_ld_p4, v_l_ld_g, v_l_ld_k, v_l_ld_bc, v_l_ld_hs, 0.0, &_t206, &_t207, &_t208, &_t209, &_t210, &_t211, &_t212, &_t213, &_t214, &_t215, &_t216);
              v_o12 = _t206;
              v_o24 = _t207;
              v_l_R_ld_s1 = _t208;
              v_l_R_ld_s2 = _t209;
              v_l_R_ld_s3 = _t210;
              v_l_R_ld_s4 = _t211;
              v_l_R_ld_p0 = _t212;
              v_l_R_ld_p1 = _t213;
              v_l_R_ld_p2 = _t214;
              v_l_R_ld_p3 = _t215;
              v_l_R_ld_p4 = _t216;
            }
            v_lb_R = (v_lb_R + (v_l_mld * (v_o12 + (v_l_ti * (v_o24 - v_o12)))));
        }
        if ((((double)((v_l_ast) > (0.5)))) != 0.0) {
            { double _t217, _t218, _t219, _t220, _t221, _t222; F_f_steiner(((v_li_R * (1.0 - v_l_chr)) * 1.0), (v_li_R * v_l_chr), ((v_li_R * (1.0 - v_l_chr)) * 0.0), v_l_R_st_s1, v_l_R_st_s2, v_l_R_st_d1, v_l_R_st_d2, v_l_R_st_vb, v_l_st_g, v_l_st_K, &_t217, &_t218, &_t219, &_t220, &_t221, &_t222);
              v_o1 = _t217;
              v_l_R_st_s1 = _t218;
              v_l_R_st_s2 = _t219;
              v_l_R_st_d1 = _t220;
              v_l_R_st_d2 = _t221;
              v_l_R_st_vb = _t222;
            }
            v_lb_R = (v_lb_R + ((v_l_mst * v_o1) * v_l_st_kd));
        }
        if ((((double)((v_l_ase) > (0.5)))) != 0.0) {
            { double _t223, _t224, _t225, _t226, _t227; F_f_sem(v_li_R, v_l_R_se_s1, v_l_R_se_s2, v_l_R_se_hq, v_l_R_se_bq, v_l_se_g, v_l_se_R, v_l_chr, 0.0, &_t223, &_t224, &_t225, &_t226, &_t227);
              v_o1 = _t223;
              v_l_R_se_s1 = _t224;
              v_l_R_se_s2 = _t225;
              v_l_R_se_hq = _t226;
              v_l_R_se_bq = _t227;
            }
            v_lb_R = (v_lb_R + (v_l_mse * v_o1));
        }
        if ((((double)((v_l_adi) > (0.5)))) != 0.0) {
            { double _t228, _t229, _t230, _t231, _t232, _t233, _t234, _t235, _t236, _t237, _t238; F_f_diode(v_li_R, v_l_R_di_s1, v_l_R_di_s2, v_l_R_di_s3, v_l_R_di_s4, v_l_R_di_v1, v_l_R_di_v2, v_l_R_di_v3, v_l_R_di_v4, v_l_R_di_sf, v_l_R_di_sc, v_l_di_g, v_l_di_k, v_l_di_Gf, v_l_cmp, &_t228, &_t229, &_t230, &_t231, &_t232, &_t233, &_t234, &_t235, &_t236, &_t237, &_t238);
              v_o1 = _t228;
              v_l_R_di_s1 = _t229;
              v_l_R_di_s2 = _t230;
              v_l_R_di_s3 = _t231;
              v_l_R_di_s4 = _t232;
              v_l_R_di_v1 = _t233;
              v_l_R_di_v2 = _t234;
              v_l_R_di_v3 = _t235;
              v_l_R_di_v4 = _t236;
              v_l_R_di_sf = _t237;
              v_l_R_di_sc = _t238;
            }
            v_lb_R = (v_lb_R + (v_l_mdi * v_o1));
        }
        v_e0 = v_lb_R;
        v_e1 = 0.0;
        v_e2 = 0.0;
        v_e3 = 0.0;
        if ((((double)((v_l_xa) > (0.5)))) != 0.0) {
            { double _t239, _t240, _t241, _t242, _t243; F_f_svf(v_e0, v_l_R_x0_s1, v_l_R_x0_s2, v_l_gx, 0.7071067811865476, &_t239, &_t240, &_t241, &_t242, &_t243);
              v_eh = _t239;
              v_eb = _t240;
              v_el = _t241;
              v_l_R_x0_s1 = _t242;
              v_l_R_x0_s2 = _t243;
            }
            v_l_R_x0_s1 = fixdenorm(v_l_R_x0_s1);
            v_l_R_x0_s2 = fixdenorm(v_l_R_x0_s2);
            v_e1 = v_el;
        }
        if ((((double)((v_l_xb) > (0.5)))) != 0.0) {
            { double _t244, _t245, _t246, _t247, _t248; F_f_svf(v_e1, v_l_R_x1_s1, v_l_R_x1_s2, v_l_gx, 0.7071067811865476, &_t244, &_t245, &_t246, &_t247, &_t248);
              v_eh = _t244;
              v_eb = _t245;
              v_el = _t246;
              v_l_R_x1_s1 = _t247;
              v_l_R_x1_s2 = _t248;
            }
            v_l_R_x1_s1 = fixdenorm(v_l_R_x1_s1);
            v_l_R_x1_s2 = fixdenorm(v_l_R_x1_s2);
            v_e2 = v_el;
        }
        if ((((double)((v_l_xc) > (0.5)))) != 0.0) {
            { double _t249, _t250, _t251, _t252, _t253; F_f_svf(v_e2, v_l_R_x2_s1, v_l_R_x2_s2, v_l_gx, 0.7071067811865476, &_t249, &_t250, &_t251, &_t252, &_t253);
              v_eh = _t249;
              v_eb = _t250;
              v_el = _t251;
              v_l_R_x2_s1 = _t252;
              v_l_R_x2_s2 = _t253;
            }
            v_l_R_x2_s1 = fixdenorm(v_l_R_x2_s1);
            v_l_R_x2_s2 = fixdenorm(v_l_R_x2_s2);
            v_e3 = v_el;
        }
        v_wet_R = (((((v_l_w0 * v_e0) + (v_l_w1 * v_e1)) + (v_l_w2 * v_e2)) + (v_l_w3 * v_e3)) * v_l_osc);
        v_lya_R = (v_lsrc_R + (v_l_wet * (v_wet_R - v_lsrc_R)));
    }
    v_za_L = v_lya_L;
    v_za_R = v_lya_R;
    if ((((double)((v_cur_order) < (0.5)))) != 0.0) {
        v_hya_L = v_lya_L;
        v_hya_R = v_lya_R;
        if ((((double)((v_h_run) > (0.5)))) != 0.0) {
            v_hi_L = (v_lya_L * v_h_d);
            v_hb_L = 0.0;
            if ((((double)((v_h_ash) > (0.5)))) != 0.0) {
                { double _t254, _t255, _t256, _t257, _t258, _t259, _t260, _t261, _t262; F_f_sherman(v_hi_L, v_h_L_sh_s1a, v_h_L_sh_s2a, v_h_L_sh_ba, v_h_L_sh_s1b, v_h_L_sh_s2b, v_h_L_sh_bb, v_h_L_sh_yp, v_h_sh_g, v_h_sh_R1, v_h_sh_R, v_h_sh_fb, v_h_ti, 1.0, &_t254, &_t255, &_t256, &_t257, &_t258, &_t259, &_t260, &_t261, &_t262);
                  v_o12 = _t254;
                  v_o24 = _t255;
                  v_h_L_sh_s1a = _t256;
                  v_h_L_sh_s2a = _t257;
                  v_h_L_sh_ba = _t258;
                  v_h_L_sh_s1b = _t259;
                  v_h_L_sh_s2b = _t260;
                  v_h_L_sh_bb = _t261;
                  v_h_L_sh_yp = _t262;
                }
                v_hb_L = (v_hb_L + (v_h_msh * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_h_ak3) > (0.5)))) != 0.0) {
                { double _t263, _t264, _t265, _t266, _t267; F_f_k35hp(v_hi_L, v_h_L_k3_s1, v_h_L_k3_s2, v_h_L_k3_s3, v_h_L_k3_yp, v_h_k3_g, v_h_k3_K, v_h_k3_L, &_t263, &_t264, &_t265, &_t266, &_t267);
                  v_o1 = _t263;
                  v_h_L_k3_s1 = _t264;
                  v_h_L_k3_s2 = _t265;
                  v_h_L_k3_s3 = _t266;
                  v_h_L_k3_yp = _t267;
                }
                v_hb_L = (v_hb_L + (v_h_mk3 * v_o1));
            }
            if ((((double)((v_h_ald) > (0.5)))) != 0.0) {
                { double _t268, _t269, _t270, _t271, _t272, _t273, _t274, _t275, _t276, _t277, _t278; F_f_ladder(v_hi_L, v_h_L_ld_s1, v_h_L_ld_s2, v_h_L_ld_s3, v_h_L_ld_s4, v_h_L_ld_p0, v_h_L_ld_p1, v_h_L_ld_p2, v_h_L_ld_p3, v_h_L_ld_p4, v_h_ld_g, v_h_ld_k, v_h_ld_bc, v_h_ld_hs, 1.0, &_t268, &_t269, &_t270, &_t271, &_t272, &_t273, &_t274, &_t275, &_t276, &_t277, &_t278);
                  v_o12 = _t268;
                  v_o24 = _t269;
                  v_h_L_ld_s1 = _t270;
                  v_h_L_ld_s2 = _t271;
                  v_h_L_ld_s3 = _t272;
                  v_h_L_ld_s4 = _t273;
                  v_h_L_ld_p0 = _t274;
                  v_h_L_ld_p1 = _t275;
                  v_h_L_ld_p2 = _t276;
                  v_h_L_ld_p3 = _t277;
                  v_h_L_ld_p4 = _t278;
                }
                v_hb_L = (v_hb_L + (v_h_mld * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_h_ast) > (0.5)))) != 0.0) {
                { double _t279, _t280, _t281, _t282, _t283, _t284; F_f_steiner(((v_hi_L * (1.0 - v_h_chr)) * 0.0), (v_hi_L * v_h_chr), ((v_hi_L * (1.0 - v_h_chr)) * 1.0), v_h_L_st_s1, v_h_L_st_s2, v_h_L_st_d1, v_h_L_st_d2, v_h_L_st_vb, v_h_st_g, v_h_st_K, &_t279, &_t280, &_t281, &_t282, &_t283, &_t284);
                  v_o1 = _t279;
                  v_h_L_st_s1 = _t280;
                  v_h_L_st_s2 = _t281;
                  v_h_L_st_d1 = _t282;
                  v_h_L_st_d2 = _t283;
                  v_h_L_st_vb = _t284;
                }
                v_hb_L = (v_hb_L + ((v_h_mst * v_o1) * v_h_st_kd));
            }
            if ((((double)((v_h_ase) > (0.5)))) != 0.0) {
                { double _t285, _t286, _t287, _t288, _t289; F_f_sem(v_hi_L, v_h_L_se_s1, v_h_L_se_s2, v_h_L_se_hq, v_h_L_se_bq, v_h_se_g, v_h_se_R, v_h_chr, 1.0, &_t285, &_t286, &_t287, &_t288, &_t289);
                  v_o1 = _t285;
                  v_h_L_se_s1 = _t286;
                  v_h_L_se_s2 = _t287;
                  v_h_L_se_hq = _t288;
                  v_h_L_se_bq = _t289;
                }
                v_hb_L = (v_hb_L + (v_h_mse * v_o1));
            }
            v_e0 = v_hb_L;
            v_e1 = 0.0;
            v_e2 = 0.0;
            v_e3 = 0.0;
            if ((((double)((v_h_xa) > (0.5)))) != 0.0) {
                { double _t290, _t291, _t292, _t293, _t294; F_f_svf(v_e0, v_h_L_x0_s1, v_h_L_x0_s2, v_h_gx, 0.7071067811865476, &_t290, &_t291, &_t292, &_t293, &_t294);
                  v_eh = _t290;
                  v_eb = _t291;
                  v_el = _t292;
                  v_h_L_x0_s1 = _t293;
                  v_h_L_x0_s2 = _t294;
                }
                v_h_L_x0_s1 = fixdenorm(v_h_L_x0_s1);
                v_h_L_x0_s2 = fixdenorm(v_h_L_x0_s2);
                v_e1 = v_eh;
            }
            if ((((double)((v_h_xb) > (0.5)))) != 0.0) {
                { double _t295, _t296, _t297, _t298, _t299; F_f_svf(v_e1, v_h_L_x1_s1, v_h_L_x1_s2, v_h_gx, 0.7071067811865476, &_t295, &_t296, &_t297, &_t298, &_t299);
                  v_eh = _t295;
                  v_eb = _t296;
                  v_el = _t297;
                  v_h_L_x1_s1 = _t298;
                  v_h_L_x1_s2 = _t299;
                }
                v_h_L_x1_s1 = fixdenorm(v_h_L_x1_s1);
                v_h_L_x1_s2 = fixdenorm(v_h_L_x1_s2);
                v_e2 = v_eh;
            }
            if ((((double)((v_h_xc) > (0.5)))) != 0.0) {
                { double _t300, _t301, _t302, _t303, _t304; F_f_svf(v_e2, v_h_L_x2_s1, v_h_L_x2_s2, v_h_gx, 0.7071067811865476, &_t300, &_t301, &_t302, &_t303, &_t304);
                  v_eh = _t300;
                  v_eb = _t301;
                  v_el = _t302;
                  v_h_L_x2_s1 = _t303;
                  v_h_L_x2_s2 = _t304;
                }
                v_h_L_x2_s1 = fixdenorm(v_h_L_x2_s1);
                v_h_L_x2_s2 = fixdenorm(v_h_L_x2_s2);
                v_e3 = v_eh;
            }
            v_wet_L = (((((v_h_w0 * v_e0) + (v_h_w1 * v_e1)) + (v_h_w2 * v_e2)) + (v_h_w3 * v_e3)) * v_h_osc);
            v_hya_L = (v_lya_L + (v_h_wet * (v_wet_L - v_lya_L)));
            v_hi_R = (v_lya_R * v_h_d);
            v_hb_R = 0.0;
            if ((((double)((v_h_ash) > (0.5)))) != 0.0) {
                { double _t305, _t306, _t307, _t308, _t309, _t310, _t311, _t312, _t313; F_f_sherman(v_hi_R, v_h_R_sh_s1a, v_h_R_sh_s2a, v_h_R_sh_ba, v_h_R_sh_s1b, v_h_R_sh_s2b, v_h_R_sh_bb, v_h_R_sh_yp, v_h_sh_g, v_h_sh_R1, v_h_sh_R, v_h_sh_fb, v_h_ti, 1.0, &_t305, &_t306, &_t307, &_t308, &_t309, &_t310, &_t311, &_t312, &_t313);
                  v_o12 = _t305;
                  v_o24 = _t306;
                  v_h_R_sh_s1a = _t307;
                  v_h_R_sh_s2a = _t308;
                  v_h_R_sh_ba = _t309;
                  v_h_R_sh_s1b = _t310;
                  v_h_R_sh_s2b = _t311;
                  v_h_R_sh_bb = _t312;
                  v_h_R_sh_yp = _t313;
                }
                v_hb_R = (v_hb_R + (v_h_msh * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_h_ak3) > (0.5)))) != 0.0) {
                { double _t314, _t315, _t316, _t317, _t318; F_f_k35hp(v_hi_R, v_h_R_k3_s1, v_h_R_k3_s2, v_h_R_k3_s3, v_h_R_k3_yp, v_h_k3_g, v_h_k3_K, v_h_k3_L, &_t314, &_t315, &_t316, &_t317, &_t318);
                  v_o1 = _t314;
                  v_h_R_k3_s1 = _t315;
                  v_h_R_k3_s2 = _t316;
                  v_h_R_k3_s3 = _t317;
                  v_h_R_k3_yp = _t318;
                }
                v_hb_R = (v_hb_R + (v_h_mk3 * v_o1));
            }
            if ((((double)((v_h_ald) > (0.5)))) != 0.0) {
                { double _t319, _t320, _t321, _t322, _t323, _t324, _t325, _t326, _t327, _t328, _t329; F_f_ladder(v_hi_R, v_h_R_ld_s1, v_h_R_ld_s2, v_h_R_ld_s3, v_h_R_ld_s4, v_h_R_ld_p0, v_h_R_ld_p1, v_h_R_ld_p2, v_h_R_ld_p3, v_h_R_ld_p4, v_h_ld_g, v_h_ld_k, v_h_ld_bc, v_h_ld_hs, 1.0, &_t319, &_t320, &_t321, &_t322, &_t323, &_t324, &_t325, &_t326, &_t327, &_t328, &_t329);
                  v_o12 = _t319;
                  v_o24 = _t320;
                  v_h_R_ld_s1 = _t321;
                  v_h_R_ld_s2 = _t322;
                  v_h_R_ld_s3 = _t323;
                  v_h_R_ld_s4 = _t324;
                  v_h_R_ld_p0 = _t325;
                  v_h_R_ld_p1 = _t326;
                  v_h_R_ld_p2 = _t327;
                  v_h_R_ld_p3 = _t328;
                  v_h_R_ld_p4 = _t329;
                }
                v_hb_R = (v_hb_R + (v_h_mld * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_h_ast) > (0.5)))) != 0.0) {
                { double _t330, _t331, _t332, _t333, _t334, _t335; F_f_steiner(((v_hi_R * (1.0 - v_h_chr)) * 0.0), (v_hi_R * v_h_chr), ((v_hi_R * (1.0 - v_h_chr)) * 1.0), v_h_R_st_s1, v_h_R_st_s2, v_h_R_st_d1, v_h_R_st_d2, v_h_R_st_vb, v_h_st_g, v_h_st_K, &_t330, &_t331, &_t332, &_t333, &_t334, &_t335);
                  v_o1 = _t330;
                  v_h_R_st_s1 = _t331;
                  v_h_R_st_s2 = _t332;
                  v_h_R_st_d1 = _t333;
                  v_h_R_st_d2 = _t334;
                  v_h_R_st_vb = _t335;
                }
                v_hb_R = (v_hb_R + ((v_h_mst * v_o1) * v_h_st_kd));
            }
            if ((((double)((v_h_ase) > (0.5)))) != 0.0) {
                { double _t336, _t337, _t338, _t339, _t340; F_f_sem(v_hi_R, v_h_R_se_s1, v_h_R_se_s2, v_h_R_se_hq, v_h_R_se_bq, v_h_se_g, v_h_se_R, v_h_chr, 1.0, &_t336, &_t337, &_t338, &_t339, &_t340);
                  v_o1 = _t336;
                  v_h_R_se_s1 = _t337;
                  v_h_R_se_s2 = _t338;
                  v_h_R_se_hq = _t339;
                  v_h_R_se_bq = _t340;
                }
                v_hb_R = (v_hb_R + (v_h_mse * v_o1));
            }
            v_e0 = v_hb_R;
            v_e1 = 0.0;
            v_e2 = 0.0;
            v_e3 = 0.0;
            if ((((double)((v_h_xa) > (0.5)))) != 0.0) {
                { double _t341, _t342, _t343, _t344, _t345; F_f_svf(v_e0, v_h_R_x0_s1, v_h_R_x0_s2, v_h_gx, 0.7071067811865476, &_t341, &_t342, &_t343, &_t344, &_t345);
                  v_eh = _t341;
                  v_eb = _t342;
                  v_el = _t343;
                  v_h_R_x0_s1 = _t344;
                  v_h_R_x0_s2 = _t345;
                }
                v_h_R_x0_s1 = fixdenorm(v_h_R_x0_s1);
                v_h_R_x0_s2 = fixdenorm(v_h_R_x0_s2);
                v_e1 = v_eh;
            }
            if ((((double)((v_h_xb) > (0.5)))) != 0.0) {
                { double _t346, _t347, _t348, _t349, _t350; F_f_svf(v_e1, v_h_R_x1_s1, v_h_R_x1_s2, v_h_gx, 0.7071067811865476, &_t346, &_t347, &_t348, &_t349, &_t350);
                  v_eh = _t346;
                  v_eb = _t347;
                  v_el = _t348;
                  v_h_R_x1_s1 = _t349;
                  v_h_R_x1_s2 = _t350;
                }
                v_h_R_x1_s1 = fixdenorm(v_h_R_x1_s1);
                v_h_R_x1_s2 = fixdenorm(v_h_R_x1_s2);
                v_e2 = v_eh;
            }
            if ((((double)((v_h_xc) > (0.5)))) != 0.0) {
                { double _t351, _t352, _t353, _t354, _t355; F_f_svf(v_e2, v_h_R_x2_s1, v_h_R_x2_s2, v_h_gx, 0.7071067811865476, &_t351, &_t352, &_t353, &_t354, &_t355);
                  v_eh = _t351;
                  v_eb = _t352;
                  v_el = _t353;
                  v_h_R_x2_s1 = _t354;
                  v_h_R_x2_s2 = _t355;
                }
                v_h_R_x2_s1 = fixdenorm(v_h_R_x2_s1);
                v_h_R_x2_s2 = fixdenorm(v_h_R_x2_s2);
                v_e3 = v_eh;
            }
            v_wet_R = (((((v_h_w0 * v_e0) + (v_h_w1 * v_e1)) + (v_h_w2 * v_e2)) + (v_h_w3 * v_e3)) * v_h_osc);
            v_hya_R = (v_lya_R + (v_h_wet * (v_wet_R - v_lya_R)));
        }
        v_za_L = v_hya_L;
        v_za_R = v_hya_R;
    }
    if ((((double)((v_ovs) > (1.5)))) != 0.0) {
        v_hyb_L = 0.0;
        v_hyb_R = 0.0;
        if ((((double)((v_cur_order) > (0.5)))) != 0.0) {
            v_hyb_L = v_xb_L;
            v_hyb_R = v_xb_R;
            if ((((double)((v_h_run) > (0.5)))) != 0.0) {
                v_hi_L = (v_xb_L * v_h_d);
                v_hb_L = 0.0;
                if ((((double)((v_h_ash) > (0.5)))) != 0.0) {
                    { double _t356, _t357, _t358, _t359, _t360, _t361, _t362, _t363, _t364; F_f_sherman(v_hi_L, v_h_L_sh_s1a, v_h_L_sh_s2a, v_h_L_sh_ba, v_h_L_sh_s1b, v_h_L_sh_s2b, v_h_L_sh_bb, v_h_L_sh_yp, v_h_sh_g, v_h_sh_R1, v_h_sh_R, v_h_sh_fb, v_h_ti, 1.0, &_t356, &_t357, &_t358, &_t359, &_t360, &_t361, &_t362, &_t363, &_t364);
                      v_o12 = _t356;
                      v_o24 = _t357;
                      v_h_L_sh_s1a = _t358;
                      v_h_L_sh_s2a = _t359;
                      v_h_L_sh_ba = _t360;
                      v_h_L_sh_s1b = _t361;
                      v_h_L_sh_s2b = _t362;
                      v_h_L_sh_bb = _t363;
                      v_h_L_sh_yp = _t364;
                    }
                    v_hb_L = (v_hb_L + (v_h_msh * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
                }
                if ((((double)((v_h_ak3) > (0.5)))) != 0.0) {
                    { double _t365, _t366, _t367, _t368, _t369; F_f_k35hp(v_hi_L, v_h_L_k3_s1, v_h_L_k3_s2, v_h_L_k3_s3, v_h_L_k3_yp, v_h_k3_g, v_h_k3_K, v_h_k3_L, &_t365, &_t366, &_t367, &_t368, &_t369);
                      v_o1 = _t365;
                      v_h_L_k3_s1 = _t366;
                      v_h_L_k3_s2 = _t367;
                      v_h_L_k3_s3 = _t368;
                      v_h_L_k3_yp = _t369;
                    }
                    v_hb_L = (v_hb_L + (v_h_mk3 * v_o1));
                }
                if ((((double)((v_h_ald) > (0.5)))) != 0.0) {
                    { double _t370, _t371, _t372, _t373, _t374, _t375, _t376, _t377, _t378, _t379, _t380; F_f_ladder(v_hi_L, v_h_L_ld_s1, v_h_L_ld_s2, v_h_L_ld_s3, v_h_L_ld_s4, v_h_L_ld_p0, v_h_L_ld_p1, v_h_L_ld_p2, v_h_L_ld_p3, v_h_L_ld_p4, v_h_ld_g, v_h_ld_k, v_h_ld_bc, v_h_ld_hs, 1.0, &_t370, &_t371, &_t372, &_t373, &_t374, &_t375, &_t376, &_t377, &_t378, &_t379, &_t380);
                      v_o12 = _t370;
                      v_o24 = _t371;
                      v_h_L_ld_s1 = _t372;
                      v_h_L_ld_s2 = _t373;
                      v_h_L_ld_s3 = _t374;
                      v_h_L_ld_s4 = _t375;
                      v_h_L_ld_p0 = _t376;
                      v_h_L_ld_p1 = _t377;
                      v_h_L_ld_p2 = _t378;
                      v_h_L_ld_p3 = _t379;
                      v_h_L_ld_p4 = _t380;
                    }
                    v_hb_L = (v_hb_L + (v_h_mld * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
                }
                if ((((double)((v_h_ast) > (0.5)))) != 0.0) {
                    { double _t381, _t382, _t383, _t384, _t385, _t386; F_f_steiner(((v_hi_L * (1.0 - v_h_chr)) * 0.0), (v_hi_L * v_h_chr), ((v_hi_L * (1.0 - v_h_chr)) * 1.0), v_h_L_st_s1, v_h_L_st_s2, v_h_L_st_d1, v_h_L_st_d2, v_h_L_st_vb, v_h_st_g, v_h_st_K, &_t381, &_t382, &_t383, &_t384, &_t385, &_t386);
                      v_o1 = _t381;
                      v_h_L_st_s1 = _t382;
                      v_h_L_st_s2 = _t383;
                      v_h_L_st_d1 = _t384;
                      v_h_L_st_d2 = _t385;
                      v_h_L_st_vb = _t386;
                    }
                    v_hb_L = (v_hb_L + ((v_h_mst * v_o1) * v_h_st_kd));
                }
                if ((((double)((v_h_ase) > (0.5)))) != 0.0) {
                    { double _t387, _t388, _t389, _t390, _t391; F_f_sem(v_hi_L, v_h_L_se_s1, v_h_L_se_s2, v_h_L_se_hq, v_h_L_se_bq, v_h_se_g, v_h_se_R, v_h_chr, 1.0, &_t387, &_t388, &_t389, &_t390, &_t391);
                      v_o1 = _t387;
                      v_h_L_se_s1 = _t388;
                      v_h_L_se_s2 = _t389;
                      v_h_L_se_hq = _t390;
                      v_h_L_se_bq = _t391;
                    }
                    v_hb_L = (v_hb_L + (v_h_mse * v_o1));
                }
                v_e0 = v_hb_L;
                v_e1 = 0.0;
                v_e2 = 0.0;
                v_e3 = 0.0;
                if ((((double)((v_h_xa) > (0.5)))) != 0.0) {
                    { double _t392, _t393, _t394, _t395, _t396; F_f_svf(v_e0, v_h_L_x0_s1, v_h_L_x0_s2, v_h_gx, 0.7071067811865476, &_t392, &_t393, &_t394, &_t395, &_t396);
                      v_eh = _t392;
                      v_eb = _t393;
                      v_el = _t394;
                      v_h_L_x0_s1 = _t395;
                      v_h_L_x0_s2 = _t396;
                    }
                    v_h_L_x0_s1 = fixdenorm(v_h_L_x0_s1);
                    v_h_L_x0_s2 = fixdenorm(v_h_L_x0_s2);
                    v_e1 = v_eh;
                }
                if ((((double)((v_h_xb) > (0.5)))) != 0.0) {
                    { double _t397, _t398, _t399, _t400, _t401; F_f_svf(v_e1, v_h_L_x1_s1, v_h_L_x1_s2, v_h_gx, 0.7071067811865476, &_t397, &_t398, &_t399, &_t400, &_t401);
                      v_eh = _t397;
                      v_eb = _t398;
                      v_el = _t399;
                      v_h_L_x1_s1 = _t400;
                      v_h_L_x1_s2 = _t401;
                    }
                    v_h_L_x1_s1 = fixdenorm(v_h_L_x1_s1);
                    v_h_L_x1_s2 = fixdenorm(v_h_L_x1_s2);
                    v_e2 = v_eh;
                }
                if ((((double)((v_h_xc) > (0.5)))) != 0.0) {
                    { double _t402, _t403, _t404, _t405, _t406; F_f_svf(v_e2, v_h_L_x2_s1, v_h_L_x2_s2, v_h_gx, 0.7071067811865476, &_t402, &_t403, &_t404, &_t405, &_t406);
                      v_eh = _t402;
                      v_eb = _t403;
                      v_el = _t404;
                      v_h_L_x2_s1 = _t405;
                      v_h_L_x2_s2 = _t406;
                    }
                    v_h_L_x2_s1 = fixdenorm(v_h_L_x2_s1);
                    v_h_L_x2_s2 = fixdenorm(v_h_L_x2_s2);
                    v_e3 = v_eh;
                }
                v_wet_L = (((((v_h_w0 * v_e0) + (v_h_w1 * v_e1)) + (v_h_w2 * v_e2)) + (v_h_w3 * v_e3)) * v_h_osc);
                v_hyb_L = (v_xb_L + (v_h_wet * (v_wet_L - v_xb_L)));
                v_hi_R = (v_xb_R * v_h_d);
                v_hb_R = 0.0;
                if ((((double)((v_h_ash) > (0.5)))) != 0.0) {
                    { double _t407, _t408, _t409, _t410, _t411, _t412, _t413, _t414, _t415; F_f_sherman(v_hi_R, v_h_R_sh_s1a, v_h_R_sh_s2a, v_h_R_sh_ba, v_h_R_sh_s1b, v_h_R_sh_s2b, v_h_R_sh_bb, v_h_R_sh_yp, v_h_sh_g, v_h_sh_R1, v_h_sh_R, v_h_sh_fb, v_h_ti, 1.0, &_t407, &_t408, &_t409, &_t410, &_t411, &_t412, &_t413, &_t414, &_t415);
                      v_o12 = _t407;
                      v_o24 = _t408;
                      v_h_R_sh_s1a = _t409;
                      v_h_R_sh_s2a = _t410;
                      v_h_R_sh_ba = _t411;
                      v_h_R_sh_s1b = _t412;
                      v_h_R_sh_s2b = _t413;
                      v_h_R_sh_bb = _t414;
                      v_h_R_sh_yp = _t415;
                    }
                    v_hb_R = (v_hb_R + (v_h_msh * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
                }
                if ((((double)((v_h_ak3) > (0.5)))) != 0.0) {
                    { double _t416, _t417, _t418, _t419, _t420; F_f_k35hp(v_hi_R, v_h_R_k3_s1, v_h_R_k3_s2, v_h_R_k3_s3, v_h_R_k3_yp, v_h_k3_g, v_h_k3_K, v_h_k3_L, &_t416, &_t417, &_t418, &_t419, &_t420);
                      v_o1 = _t416;
                      v_h_R_k3_s1 = _t417;
                      v_h_R_k3_s2 = _t418;
                      v_h_R_k3_s3 = _t419;
                      v_h_R_k3_yp = _t420;
                    }
                    v_hb_R = (v_hb_R + (v_h_mk3 * v_o1));
                }
                if ((((double)((v_h_ald) > (0.5)))) != 0.0) {
                    { double _t421, _t422, _t423, _t424, _t425, _t426, _t427, _t428, _t429, _t430, _t431; F_f_ladder(v_hi_R, v_h_R_ld_s1, v_h_R_ld_s2, v_h_R_ld_s3, v_h_R_ld_s4, v_h_R_ld_p0, v_h_R_ld_p1, v_h_R_ld_p2, v_h_R_ld_p3, v_h_R_ld_p4, v_h_ld_g, v_h_ld_k, v_h_ld_bc, v_h_ld_hs, 1.0, &_t421, &_t422, &_t423, &_t424, &_t425, &_t426, &_t427, &_t428, &_t429, &_t430, &_t431);
                      v_o12 = _t421;
                      v_o24 = _t422;
                      v_h_R_ld_s1 = _t423;
                      v_h_R_ld_s2 = _t424;
                      v_h_R_ld_s3 = _t425;
                      v_h_R_ld_s4 = _t426;
                      v_h_R_ld_p0 = _t427;
                      v_h_R_ld_p1 = _t428;
                      v_h_R_ld_p2 = _t429;
                      v_h_R_ld_p3 = _t430;
                      v_h_R_ld_p4 = _t431;
                    }
                    v_hb_R = (v_hb_R + (v_h_mld * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
                }
                if ((((double)((v_h_ast) > (0.5)))) != 0.0) {
                    { double _t432, _t433, _t434, _t435, _t436, _t437; F_f_steiner(((v_hi_R * (1.0 - v_h_chr)) * 0.0), (v_hi_R * v_h_chr), ((v_hi_R * (1.0 - v_h_chr)) * 1.0), v_h_R_st_s1, v_h_R_st_s2, v_h_R_st_d1, v_h_R_st_d2, v_h_R_st_vb, v_h_st_g, v_h_st_K, &_t432, &_t433, &_t434, &_t435, &_t436, &_t437);
                      v_o1 = _t432;
                      v_h_R_st_s1 = _t433;
                      v_h_R_st_s2 = _t434;
                      v_h_R_st_d1 = _t435;
                      v_h_R_st_d2 = _t436;
                      v_h_R_st_vb = _t437;
                    }
                    v_hb_R = (v_hb_R + ((v_h_mst * v_o1) * v_h_st_kd));
                }
                if ((((double)((v_h_ase) > (0.5)))) != 0.0) {
                    { double _t438, _t439, _t440, _t441, _t442; F_f_sem(v_hi_R, v_h_R_se_s1, v_h_R_se_s2, v_h_R_se_hq, v_h_R_se_bq, v_h_se_g, v_h_se_R, v_h_chr, 1.0, &_t438, &_t439, &_t440, &_t441, &_t442);
                      v_o1 = _t438;
                      v_h_R_se_s1 = _t439;
                      v_h_R_se_s2 = _t440;
                      v_h_R_se_hq = _t441;
                      v_h_R_se_bq = _t442;
                    }
                    v_hb_R = (v_hb_R + (v_h_mse * v_o1));
                }
                v_e0 = v_hb_R;
                v_e1 = 0.0;
                v_e2 = 0.0;
                v_e3 = 0.0;
                if ((((double)((v_h_xa) > (0.5)))) != 0.0) {
                    { double _t443, _t444, _t445, _t446, _t447; F_f_svf(v_e0, v_h_R_x0_s1, v_h_R_x0_s2, v_h_gx, 0.7071067811865476, &_t443, &_t444, &_t445, &_t446, &_t447);
                      v_eh = _t443;
                      v_eb = _t444;
                      v_el = _t445;
                      v_h_R_x0_s1 = _t446;
                      v_h_R_x0_s2 = _t447;
                    }
                    v_h_R_x0_s1 = fixdenorm(v_h_R_x0_s1);
                    v_h_R_x0_s2 = fixdenorm(v_h_R_x0_s2);
                    v_e1 = v_eh;
                }
                if ((((double)((v_h_xb) > (0.5)))) != 0.0) {
                    { double _t448, _t449, _t450, _t451, _t452; F_f_svf(v_e1, v_h_R_x1_s1, v_h_R_x1_s2, v_h_gx, 0.7071067811865476, &_t448, &_t449, &_t450, &_t451, &_t452);
                      v_eh = _t448;
                      v_eb = _t449;
                      v_el = _t450;
                      v_h_R_x1_s1 = _t451;
                      v_h_R_x1_s2 = _t452;
                    }
                    v_h_R_x1_s1 = fixdenorm(v_h_R_x1_s1);
                    v_h_R_x1_s2 = fixdenorm(v_h_R_x1_s2);
                    v_e2 = v_eh;
                }
                if ((((double)((v_h_xc) > (0.5)))) != 0.0) {
                    { double _t453, _t454, _t455, _t456, _t457; F_f_svf(v_e2, v_h_R_x2_s1, v_h_R_x2_s2, v_h_gx, 0.7071067811865476, &_t453, &_t454, &_t455, &_t456, &_t457);
                      v_eh = _t453;
                      v_eb = _t454;
                      v_el = _t455;
                      v_h_R_x2_s1 = _t456;
                      v_h_R_x2_s2 = _t457;
                    }
                    v_h_R_x2_s1 = fixdenorm(v_h_R_x2_s1);
                    v_h_R_x2_s2 = fixdenorm(v_h_R_x2_s2);
                    v_e3 = v_eh;
                }
                v_wet_R = (((((v_h_w0 * v_e0) + (v_h_w1 * v_e1)) + (v_h_w2 * v_e2)) + (v_h_w3 * v_e3)) * v_h_osc);
                v_hyb_R = (v_xb_R + (v_h_wet * (v_wet_R - v_xb_R)));
            }
        }
        v_lsrc_L = ((((double)((v_cur_order) > (0.5)))) != 0.0 ? (v_hyb_L) : (v_xb_L));
        v_lsrc_R = ((((double)((v_cur_order) > (0.5)))) != 0.0 ? (v_hyb_R) : (v_xb_R));
        v_lyb_L = v_lsrc_L;
        v_lyb_R = v_lsrc_R;
        if ((((double)((v_l_run) > (0.5)))) != 0.0) {
            v_li_L = (v_lsrc_L * v_l_d);
            v_lb_L = 0.0;
            if ((((double)((v_l_ash) > (0.5)))) != 0.0) {
                { double _t458, _t459, _t460, _t461, _t462, _t463, _t464, _t465, _t466; F_f_sherman(v_li_L, v_l_L_sh_s1a, v_l_L_sh_s2a, v_l_L_sh_ba, v_l_L_sh_s1b, v_l_L_sh_s2b, v_l_L_sh_bb, v_l_L_sh_yp, v_l_sh_g, v_l_sh_R1, v_l_sh_R, v_l_sh_fb, v_l_ti, 0.0, &_t458, &_t459, &_t460, &_t461, &_t462, &_t463, &_t464, &_t465, &_t466);
                  v_o12 = _t458;
                  v_o24 = _t459;
                  v_l_L_sh_s1a = _t460;
                  v_l_L_sh_s2a = _t461;
                  v_l_L_sh_ba = _t462;
                  v_l_L_sh_s1b = _t463;
                  v_l_L_sh_s2b = _t464;
                  v_l_L_sh_bb = _t465;
                  v_l_L_sh_yp = _t466;
                }
                v_lb_L = (v_lb_L + (v_l_msh * (v_o12 + (v_l_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_l_ak3) > (0.5)))) != 0.0) {
                { double _t467, _t468, _t469, _t470, _t471; F_f_k35lp(v_li_L, v_l_L_k3_s1, v_l_L_k3_s2, v_l_L_k3_s3, v_l_L_k3_yp, v_l_k3_g, v_l_k3_K, v_l_k3_L, &_t467, &_t468, &_t469, &_t470, &_t471);
                  v_o1 = _t467;
                  v_l_L_k3_s1 = _t468;
                  v_l_L_k3_s2 = _t469;
                  v_l_L_k3_s3 = _t470;
                  v_l_L_k3_yp = _t471;
                }
                v_lb_L = (v_lb_L + (v_l_mk3 * v_o1));
            }
            if ((((double)((v_l_ald) > (0.5)))) != 0.0) {
                { double _t472, _t473, _t474, _t475, _t476, _t477, _t478, _t479, _t480, _t481, _t482; F_f_ladder(v_li_L, v_l_L_ld_s1, v_l_L_ld_s2, v_l_L_ld_s3, v_l_L_ld_s4, v_l_L_ld_p0, v_l_L_ld_p1, v_l_L_ld_p2, v_l_L_ld_p3, v_l_L_ld_p4, v_l_ld_g, v_l_ld_k, v_l_ld_bc, v_l_ld_hs, 0.0, &_t472, &_t473, &_t474, &_t475, &_t476, &_t477, &_t478, &_t479, &_t480, &_t481, &_t482);
                  v_o12 = _t472;
                  v_o24 = _t473;
                  v_l_L_ld_s1 = _t474;
                  v_l_L_ld_s2 = _t475;
                  v_l_L_ld_s3 = _t476;
                  v_l_L_ld_s4 = _t477;
                  v_l_L_ld_p0 = _t478;
                  v_l_L_ld_p1 = _t479;
                  v_l_L_ld_p2 = _t480;
                  v_l_L_ld_p3 = _t481;
                  v_l_L_ld_p4 = _t482;
                }
                v_lb_L = (v_lb_L + (v_l_mld * (v_o12 + (v_l_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_l_ast) > (0.5)))) != 0.0) {
                { double _t483, _t484, _t485, _t486, _t487, _t488; F_f_steiner(((v_li_L * (1.0 - v_l_chr)) * 1.0), (v_li_L * v_l_chr), ((v_li_L * (1.0 - v_l_chr)) * 0.0), v_l_L_st_s1, v_l_L_st_s2, v_l_L_st_d1, v_l_L_st_d2, v_l_L_st_vb, v_l_st_g, v_l_st_K, &_t483, &_t484, &_t485, &_t486, &_t487, &_t488);
                  v_o1 = _t483;
                  v_l_L_st_s1 = _t484;
                  v_l_L_st_s2 = _t485;
                  v_l_L_st_d1 = _t486;
                  v_l_L_st_d2 = _t487;
                  v_l_L_st_vb = _t488;
                }
                v_lb_L = (v_lb_L + ((v_l_mst * v_o1) * v_l_st_kd));
            }
            if ((((double)((v_l_ase) > (0.5)))) != 0.0) {
                { double _t489, _t490, _t491, _t492, _t493; F_f_sem(v_li_L, v_l_L_se_s1, v_l_L_se_s2, v_l_L_se_hq, v_l_L_se_bq, v_l_se_g, v_l_se_R, v_l_chr, 0.0, &_t489, &_t490, &_t491, &_t492, &_t493);
                  v_o1 = _t489;
                  v_l_L_se_s1 = _t490;
                  v_l_L_se_s2 = _t491;
                  v_l_L_se_hq = _t492;
                  v_l_L_se_bq = _t493;
                }
                v_lb_L = (v_lb_L + (v_l_mse * v_o1));
            }
            if ((((double)((v_l_adi) > (0.5)))) != 0.0) {
                { double _t494, _t495, _t496, _t497, _t498, _t499, _t500, _t501, _t502, _t503, _t504; F_f_diode(v_li_L, v_l_L_di_s1, v_l_L_di_s2, v_l_L_di_s3, v_l_L_di_s4, v_l_L_di_v1, v_l_L_di_v2, v_l_L_di_v3, v_l_L_di_v4, v_l_L_di_sf, v_l_L_di_sc, v_l_di_g, v_l_di_k, v_l_di_Gf, v_l_cmp, &_t494, &_t495, &_t496, &_t497, &_t498, &_t499, &_t500, &_t501, &_t502, &_t503, &_t504);
                  v_o1 = _t494;
                  v_l_L_di_s1 = _t495;
                  v_l_L_di_s2 = _t496;
                  v_l_L_di_s3 = _t497;
                  v_l_L_di_s4 = _t498;
                  v_l_L_di_v1 = _t499;
                  v_l_L_di_v2 = _t500;
                  v_l_L_di_v3 = _t501;
                  v_l_L_di_v4 = _t502;
                  v_l_L_di_sf = _t503;
                  v_l_L_di_sc = _t504;
                }
                v_lb_L = (v_lb_L + (v_l_mdi * v_o1));
            }
            v_e0 = v_lb_L;
            v_e1 = 0.0;
            v_e2 = 0.0;
            v_e3 = 0.0;
            if ((((double)((v_l_xa) > (0.5)))) != 0.0) {
                { double _t505, _t506, _t507, _t508, _t509; F_f_svf(v_e0, v_l_L_x0_s1, v_l_L_x0_s2, v_l_gx, 0.7071067811865476, &_t505, &_t506, &_t507, &_t508, &_t509);
                  v_eh = _t505;
                  v_eb = _t506;
                  v_el = _t507;
                  v_l_L_x0_s1 = _t508;
                  v_l_L_x0_s2 = _t509;
                }
                v_l_L_x0_s1 = fixdenorm(v_l_L_x0_s1);
                v_l_L_x0_s2 = fixdenorm(v_l_L_x0_s2);
                v_e1 = v_el;
            }
            if ((((double)((v_l_xb) > (0.5)))) != 0.0) {
                { double _t510, _t511, _t512, _t513, _t514; F_f_svf(v_e1, v_l_L_x1_s1, v_l_L_x1_s2, v_l_gx, 0.7071067811865476, &_t510, &_t511, &_t512, &_t513, &_t514);
                  v_eh = _t510;
                  v_eb = _t511;
                  v_el = _t512;
                  v_l_L_x1_s1 = _t513;
                  v_l_L_x1_s2 = _t514;
                }
                v_l_L_x1_s1 = fixdenorm(v_l_L_x1_s1);
                v_l_L_x1_s2 = fixdenorm(v_l_L_x1_s2);
                v_e2 = v_el;
            }
            if ((((double)((v_l_xc) > (0.5)))) != 0.0) {
                { double _t515, _t516, _t517, _t518, _t519; F_f_svf(v_e2, v_l_L_x2_s1, v_l_L_x2_s2, v_l_gx, 0.7071067811865476, &_t515, &_t516, &_t517, &_t518, &_t519);
                  v_eh = _t515;
                  v_eb = _t516;
                  v_el = _t517;
                  v_l_L_x2_s1 = _t518;
                  v_l_L_x2_s2 = _t519;
                }
                v_l_L_x2_s1 = fixdenorm(v_l_L_x2_s1);
                v_l_L_x2_s2 = fixdenorm(v_l_L_x2_s2);
                v_e3 = v_el;
            }
            v_wet_L = (((((v_l_w0 * v_e0) + (v_l_w1 * v_e1)) + (v_l_w2 * v_e2)) + (v_l_w3 * v_e3)) * v_l_osc);
            v_lyb_L = (v_lsrc_L + (v_l_wet * (v_wet_L - v_lsrc_L)));
            v_li_R = (v_lsrc_R * v_l_d);
            v_lb_R = 0.0;
            if ((((double)((v_l_ash) > (0.5)))) != 0.0) {
                { double _t520, _t521, _t522, _t523, _t524, _t525, _t526, _t527, _t528; F_f_sherman(v_li_R, v_l_R_sh_s1a, v_l_R_sh_s2a, v_l_R_sh_ba, v_l_R_sh_s1b, v_l_R_sh_s2b, v_l_R_sh_bb, v_l_R_sh_yp, v_l_sh_g, v_l_sh_R1, v_l_sh_R, v_l_sh_fb, v_l_ti, 0.0, &_t520, &_t521, &_t522, &_t523, &_t524, &_t525, &_t526, &_t527, &_t528);
                  v_o12 = _t520;
                  v_o24 = _t521;
                  v_l_R_sh_s1a = _t522;
                  v_l_R_sh_s2a = _t523;
                  v_l_R_sh_ba = _t524;
                  v_l_R_sh_s1b = _t525;
                  v_l_R_sh_s2b = _t526;
                  v_l_R_sh_bb = _t527;
                  v_l_R_sh_yp = _t528;
                }
                v_lb_R = (v_lb_R + (v_l_msh * (v_o12 + (v_l_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_l_ak3) > (0.5)))) != 0.0) {
                { double _t529, _t530, _t531, _t532, _t533; F_f_k35lp(v_li_R, v_l_R_k3_s1, v_l_R_k3_s2, v_l_R_k3_s3, v_l_R_k3_yp, v_l_k3_g, v_l_k3_K, v_l_k3_L, &_t529, &_t530, &_t531, &_t532, &_t533);
                  v_o1 = _t529;
                  v_l_R_k3_s1 = _t530;
                  v_l_R_k3_s2 = _t531;
                  v_l_R_k3_s3 = _t532;
                  v_l_R_k3_yp = _t533;
                }
                v_lb_R = (v_lb_R + (v_l_mk3 * v_o1));
            }
            if ((((double)((v_l_ald) > (0.5)))) != 0.0) {
                { double _t534, _t535, _t536, _t537, _t538, _t539, _t540, _t541, _t542, _t543, _t544; F_f_ladder(v_li_R, v_l_R_ld_s1, v_l_R_ld_s2, v_l_R_ld_s3, v_l_R_ld_s4, v_l_R_ld_p0, v_l_R_ld_p1, v_l_R_ld_p2, v_l_R_ld_p3, v_l_R_ld_p4, v_l_ld_g, v_l_ld_k, v_l_ld_bc, v_l_ld_hs, 0.0, &_t534, &_t535, &_t536, &_t537, &_t538, &_t539, &_t540, &_t541, &_t542, &_t543, &_t544);
                  v_o12 = _t534;
                  v_o24 = _t535;
                  v_l_R_ld_s1 = _t536;
                  v_l_R_ld_s2 = _t537;
                  v_l_R_ld_s3 = _t538;
                  v_l_R_ld_s4 = _t539;
                  v_l_R_ld_p0 = _t540;
                  v_l_R_ld_p1 = _t541;
                  v_l_R_ld_p2 = _t542;
                  v_l_R_ld_p3 = _t543;
                  v_l_R_ld_p4 = _t544;
                }
                v_lb_R = (v_lb_R + (v_l_mld * (v_o12 + (v_l_ti * (v_o24 - v_o12)))));
            }
            if ((((double)((v_l_ast) > (0.5)))) != 0.0) {
                { double _t545, _t546, _t547, _t548, _t549, _t550; F_f_steiner(((v_li_R * (1.0 - v_l_chr)) * 1.0), (v_li_R * v_l_chr), ((v_li_R * (1.0 - v_l_chr)) * 0.0), v_l_R_st_s1, v_l_R_st_s2, v_l_R_st_d1, v_l_R_st_d2, v_l_R_st_vb, v_l_st_g, v_l_st_K, &_t545, &_t546, &_t547, &_t548, &_t549, &_t550);
                  v_o1 = _t545;
                  v_l_R_st_s1 = _t546;
                  v_l_R_st_s2 = _t547;
                  v_l_R_st_d1 = _t548;
                  v_l_R_st_d2 = _t549;
                  v_l_R_st_vb = _t550;
                }
                v_lb_R = (v_lb_R + ((v_l_mst * v_o1) * v_l_st_kd));
            }
            if ((((double)((v_l_ase) > (0.5)))) != 0.0) {
                { double _t551, _t552, _t553, _t554, _t555; F_f_sem(v_li_R, v_l_R_se_s1, v_l_R_se_s2, v_l_R_se_hq, v_l_R_se_bq, v_l_se_g, v_l_se_R, v_l_chr, 0.0, &_t551, &_t552, &_t553, &_t554, &_t555);
                  v_o1 = _t551;
                  v_l_R_se_s1 = _t552;
                  v_l_R_se_s2 = _t553;
                  v_l_R_se_hq = _t554;
                  v_l_R_se_bq = _t555;
                }
                v_lb_R = (v_lb_R + (v_l_mse * v_o1));
            }
            if ((((double)((v_l_adi) > (0.5)))) != 0.0) {
                { double _t556, _t557, _t558, _t559, _t560, _t561, _t562, _t563, _t564, _t565, _t566; F_f_diode(v_li_R, v_l_R_di_s1, v_l_R_di_s2, v_l_R_di_s3, v_l_R_di_s4, v_l_R_di_v1, v_l_R_di_v2, v_l_R_di_v3, v_l_R_di_v4, v_l_R_di_sf, v_l_R_di_sc, v_l_di_g, v_l_di_k, v_l_di_Gf, v_l_cmp, &_t556, &_t557, &_t558, &_t559, &_t560, &_t561, &_t562, &_t563, &_t564, &_t565, &_t566);
                  v_o1 = _t556;
                  v_l_R_di_s1 = _t557;
                  v_l_R_di_s2 = _t558;
                  v_l_R_di_s3 = _t559;
                  v_l_R_di_s4 = _t560;
                  v_l_R_di_v1 = _t561;
                  v_l_R_di_v2 = _t562;
                  v_l_R_di_v3 = _t563;
                  v_l_R_di_v4 = _t564;
                  v_l_R_di_sf = _t565;
                  v_l_R_di_sc = _t566;
                }
                v_lb_R = (v_lb_R + (v_l_mdi * v_o1));
            }
            v_e0 = v_lb_R;
            v_e1 = 0.0;
            v_e2 = 0.0;
            v_e3 = 0.0;
            if ((((double)((v_l_xa) > (0.5)))) != 0.0) {
                { double _t567, _t568, _t569, _t570, _t571; F_f_svf(v_e0, v_l_R_x0_s1, v_l_R_x0_s2, v_l_gx, 0.7071067811865476, &_t567, &_t568, &_t569, &_t570, &_t571);
                  v_eh = _t567;
                  v_eb = _t568;
                  v_el = _t569;
                  v_l_R_x0_s1 = _t570;
                  v_l_R_x0_s2 = _t571;
                }
                v_l_R_x0_s1 = fixdenorm(v_l_R_x0_s1);
                v_l_R_x0_s2 = fixdenorm(v_l_R_x0_s2);
                v_e1 = v_el;
            }
            if ((((double)((v_l_xb) > (0.5)))) != 0.0) {
                { double _t572, _t573, _t574, _t575, _t576; F_f_svf(v_e1, v_l_R_x1_s1, v_l_R_x1_s2, v_l_gx, 0.7071067811865476, &_t572, &_t573, &_t574, &_t575, &_t576);
                  v_eh = _t572;
                  v_eb = _t573;
                  v_el = _t574;
                  v_l_R_x1_s1 = _t575;
                  v_l_R_x1_s2 = _t576;
                }
                v_l_R_x1_s1 = fixdenorm(v_l_R_x1_s1);
                v_l_R_x1_s2 = fixdenorm(v_l_R_x1_s2);
                v_e2 = v_el;
            }
            if ((((double)((v_l_xc) > (0.5)))) != 0.0) {
                { double _t577, _t578, _t579, _t580, _t581; F_f_svf(v_e2, v_l_R_x2_s1, v_l_R_x2_s2, v_l_gx, 0.7071067811865476, &_t577, &_t578, &_t579, &_t580, &_t581);
                  v_eh = _t577;
                  v_eb = _t578;
                  v_el = _t579;
                  v_l_R_x2_s1 = _t580;
                  v_l_R_x2_s2 = _t581;
                }
                v_l_R_x2_s1 = fixdenorm(v_l_R_x2_s1);
                v_l_R_x2_s2 = fixdenorm(v_l_R_x2_s2);
                v_e3 = v_el;
            }
            v_wet_R = (((((v_l_w0 * v_e0) + (v_l_w1 * v_e1)) + (v_l_w2 * v_e2)) + (v_l_w3 * v_e3)) * v_l_osc);
            v_lyb_R = (v_lsrc_R + (v_l_wet * (v_wet_R - v_lsrc_R)));
        }
        v_zb_L = v_lyb_L;
        v_zb_R = v_lyb_R;
        if ((((double)((v_cur_order) < (0.5)))) != 0.0) {
            v_hyb_L = v_lyb_L;
            v_hyb_R = v_lyb_R;
            if ((((double)((v_h_run) > (0.5)))) != 0.0) {
                v_hi_L = (v_lyb_L * v_h_d);
                v_hb_L = 0.0;
                if ((((double)((v_h_ash) > (0.5)))) != 0.0) {
                    { double _t582, _t583, _t584, _t585, _t586, _t587, _t588, _t589, _t590; F_f_sherman(v_hi_L, v_h_L_sh_s1a, v_h_L_sh_s2a, v_h_L_sh_ba, v_h_L_sh_s1b, v_h_L_sh_s2b, v_h_L_sh_bb, v_h_L_sh_yp, v_h_sh_g, v_h_sh_R1, v_h_sh_R, v_h_sh_fb, v_h_ti, 1.0, &_t582, &_t583, &_t584, &_t585, &_t586, &_t587, &_t588, &_t589, &_t590);
                      v_o12 = _t582;
                      v_o24 = _t583;
                      v_h_L_sh_s1a = _t584;
                      v_h_L_sh_s2a = _t585;
                      v_h_L_sh_ba = _t586;
                      v_h_L_sh_s1b = _t587;
                      v_h_L_sh_s2b = _t588;
                      v_h_L_sh_bb = _t589;
                      v_h_L_sh_yp = _t590;
                    }
                    v_hb_L = (v_hb_L + (v_h_msh * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
                }
                if ((((double)((v_h_ak3) > (0.5)))) != 0.0) {
                    { double _t591, _t592, _t593, _t594, _t595; F_f_k35hp(v_hi_L, v_h_L_k3_s1, v_h_L_k3_s2, v_h_L_k3_s3, v_h_L_k3_yp, v_h_k3_g, v_h_k3_K, v_h_k3_L, &_t591, &_t592, &_t593, &_t594, &_t595);
                      v_o1 = _t591;
                      v_h_L_k3_s1 = _t592;
                      v_h_L_k3_s2 = _t593;
                      v_h_L_k3_s3 = _t594;
                      v_h_L_k3_yp = _t595;
                    }
                    v_hb_L = (v_hb_L + (v_h_mk3 * v_o1));
                }
                if ((((double)((v_h_ald) > (0.5)))) != 0.0) {
                    { double _t596, _t597, _t598, _t599, _t600, _t601, _t602, _t603, _t604, _t605, _t606; F_f_ladder(v_hi_L, v_h_L_ld_s1, v_h_L_ld_s2, v_h_L_ld_s3, v_h_L_ld_s4, v_h_L_ld_p0, v_h_L_ld_p1, v_h_L_ld_p2, v_h_L_ld_p3, v_h_L_ld_p4, v_h_ld_g, v_h_ld_k, v_h_ld_bc, v_h_ld_hs, 1.0, &_t596, &_t597, &_t598, &_t599, &_t600, &_t601, &_t602, &_t603, &_t604, &_t605, &_t606);
                      v_o12 = _t596;
                      v_o24 = _t597;
                      v_h_L_ld_s1 = _t598;
                      v_h_L_ld_s2 = _t599;
                      v_h_L_ld_s3 = _t600;
                      v_h_L_ld_s4 = _t601;
                      v_h_L_ld_p0 = _t602;
                      v_h_L_ld_p1 = _t603;
                      v_h_L_ld_p2 = _t604;
                      v_h_L_ld_p3 = _t605;
                      v_h_L_ld_p4 = _t606;
                    }
                    v_hb_L = (v_hb_L + (v_h_mld * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
                }
                if ((((double)((v_h_ast) > (0.5)))) != 0.0) {
                    { double _t607, _t608, _t609, _t610, _t611, _t612; F_f_steiner(((v_hi_L * (1.0 - v_h_chr)) * 0.0), (v_hi_L * v_h_chr), ((v_hi_L * (1.0 - v_h_chr)) * 1.0), v_h_L_st_s1, v_h_L_st_s2, v_h_L_st_d1, v_h_L_st_d2, v_h_L_st_vb, v_h_st_g, v_h_st_K, &_t607, &_t608, &_t609, &_t610, &_t611, &_t612);
                      v_o1 = _t607;
                      v_h_L_st_s1 = _t608;
                      v_h_L_st_s2 = _t609;
                      v_h_L_st_d1 = _t610;
                      v_h_L_st_d2 = _t611;
                      v_h_L_st_vb = _t612;
                    }
                    v_hb_L = (v_hb_L + ((v_h_mst * v_o1) * v_h_st_kd));
                }
                if ((((double)((v_h_ase) > (0.5)))) != 0.0) {
                    { double _t613, _t614, _t615, _t616, _t617; F_f_sem(v_hi_L, v_h_L_se_s1, v_h_L_se_s2, v_h_L_se_hq, v_h_L_se_bq, v_h_se_g, v_h_se_R, v_h_chr, 1.0, &_t613, &_t614, &_t615, &_t616, &_t617);
                      v_o1 = _t613;
                      v_h_L_se_s1 = _t614;
                      v_h_L_se_s2 = _t615;
                      v_h_L_se_hq = _t616;
                      v_h_L_se_bq = _t617;
                    }
                    v_hb_L = (v_hb_L + (v_h_mse * v_o1));
                }
                v_e0 = v_hb_L;
                v_e1 = 0.0;
                v_e2 = 0.0;
                v_e3 = 0.0;
                if ((((double)((v_h_xa) > (0.5)))) != 0.0) {
                    { double _t618, _t619, _t620, _t621, _t622; F_f_svf(v_e0, v_h_L_x0_s1, v_h_L_x0_s2, v_h_gx, 0.7071067811865476, &_t618, &_t619, &_t620, &_t621, &_t622);
                      v_eh = _t618;
                      v_eb = _t619;
                      v_el = _t620;
                      v_h_L_x0_s1 = _t621;
                      v_h_L_x0_s2 = _t622;
                    }
                    v_h_L_x0_s1 = fixdenorm(v_h_L_x0_s1);
                    v_h_L_x0_s2 = fixdenorm(v_h_L_x0_s2);
                    v_e1 = v_eh;
                }
                if ((((double)((v_h_xb) > (0.5)))) != 0.0) {
                    { double _t623, _t624, _t625, _t626, _t627; F_f_svf(v_e1, v_h_L_x1_s1, v_h_L_x1_s2, v_h_gx, 0.7071067811865476, &_t623, &_t624, &_t625, &_t626, &_t627);
                      v_eh = _t623;
                      v_eb = _t624;
                      v_el = _t625;
                      v_h_L_x1_s1 = _t626;
                      v_h_L_x1_s2 = _t627;
                    }
                    v_h_L_x1_s1 = fixdenorm(v_h_L_x1_s1);
                    v_h_L_x1_s2 = fixdenorm(v_h_L_x1_s2);
                    v_e2 = v_eh;
                }
                if ((((double)((v_h_xc) > (0.5)))) != 0.0) {
                    { double _t628, _t629, _t630, _t631, _t632; F_f_svf(v_e2, v_h_L_x2_s1, v_h_L_x2_s2, v_h_gx, 0.7071067811865476, &_t628, &_t629, &_t630, &_t631, &_t632);
                      v_eh = _t628;
                      v_eb = _t629;
                      v_el = _t630;
                      v_h_L_x2_s1 = _t631;
                      v_h_L_x2_s2 = _t632;
                    }
                    v_h_L_x2_s1 = fixdenorm(v_h_L_x2_s1);
                    v_h_L_x2_s2 = fixdenorm(v_h_L_x2_s2);
                    v_e3 = v_eh;
                }
                v_wet_L = (((((v_h_w0 * v_e0) + (v_h_w1 * v_e1)) + (v_h_w2 * v_e2)) + (v_h_w3 * v_e3)) * v_h_osc);
                v_hyb_L = (v_lyb_L + (v_h_wet * (v_wet_L - v_lyb_L)));
                v_hi_R = (v_lyb_R * v_h_d);
                v_hb_R = 0.0;
                if ((((double)((v_h_ash) > (0.5)))) != 0.0) {
                    { double _t633, _t634, _t635, _t636, _t637, _t638, _t639, _t640, _t641; F_f_sherman(v_hi_R, v_h_R_sh_s1a, v_h_R_sh_s2a, v_h_R_sh_ba, v_h_R_sh_s1b, v_h_R_sh_s2b, v_h_R_sh_bb, v_h_R_sh_yp, v_h_sh_g, v_h_sh_R1, v_h_sh_R, v_h_sh_fb, v_h_ti, 1.0, &_t633, &_t634, &_t635, &_t636, &_t637, &_t638, &_t639, &_t640, &_t641);
                      v_o12 = _t633;
                      v_o24 = _t634;
                      v_h_R_sh_s1a = _t635;
                      v_h_R_sh_s2a = _t636;
                      v_h_R_sh_ba = _t637;
                      v_h_R_sh_s1b = _t638;
                      v_h_R_sh_s2b = _t639;
                      v_h_R_sh_bb = _t640;
                      v_h_R_sh_yp = _t641;
                    }
                    v_hb_R = (v_hb_R + (v_h_msh * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
                }
                if ((((double)((v_h_ak3) > (0.5)))) != 0.0) {
                    { double _t642, _t643, _t644, _t645, _t646; F_f_k35hp(v_hi_R, v_h_R_k3_s1, v_h_R_k3_s2, v_h_R_k3_s3, v_h_R_k3_yp, v_h_k3_g, v_h_k3_K, v_h_k3_L, &_t642, &_t643, &_t644, &_t645, &_t646);
                      v_o1 = _t642;
                      v_h_R_k3_s1 = _t643;
                      v_h_R_k3_s2 = _t644;
                      v_h_R_k3_s3 = _t645;
                      v_h_R_k3_yp = _t646;
                    }
                    v_hb_R = (v_hb_R + (v_h_mk3 * v_o1));
                }
                if ((((double)((v_h_ald) > (0.5)))) != 0.0) {
                    { double _t647, _t648, _t649, _t650, _t651, _t652, _t653, _t654, _t655, _t656, _t657; F_f_ladder(v_hi_R, v_h_R_ld_s1, v_h_R_ld_s2, v_h_R_ld_s3, v_h_R_ld_s4, v_h_R_ld_p0, v_h_R_ld_p1, v_h_R_ld_p2, v_h_R_ld_p3, v_h_R_ld_p4, v_h_ld_g, v_h_ld_k, v_h_ld_bc, v_h_ld_hs, 1.0, &_t647, &_t648, &_t649, &_t650, &_t651, &_t652, &_t653, &_t654, &_t655, &_t656, &_t657);
                      v_o12 = _t647;
                      v_o24 = _t648;
                      v_h_R_ld_s1 = _t649;
                      v_h_R_ld_s2 = _t650;
                      v_h_R_ld_s3 = _t651;
                      v_h_R_ld_s4 = _t652;
                      v_h_R_ld_p0 = _t653;
                      v_h_R_ld_p1 = _t654;
                      v_h_R_ld_p2 = _t655;
                      v_h_R_ld_p3 = _t656;
                      v_h_R_ld_p4 = _t657;
                    }
                    v_hb_R = (v_hb_R + (v_h_mld * (v_o12 + (v_h_ti * (v_o24 - v_o12)))));
                }
                if ((((double)((v_h_ast) > (0.5)))) != 0.0) {
                    { double _t658, _t659, _t660, _t661, _t662, _t663; F_f_steiner(((v_hi_R * (1.0 - v_h_chr)) * 0.0), (v_hi_R * v_h_chr), ((v_hi_R * (1.0 - v_h_chr)) * 1.0), v_h_R_st_s1, v_h_R_st_s2, v_h_R_st_d1, v_h_R_st_d2, v_h_R_st_vb, v_h_st_g, v_h_st_K, &_t658, &_t659, &_t660, &_t661, &_t662, &_t663);
                      v_o1 = _t658;
                      v_h_R_st_s1 = _t659;
                      v_h_R_st_s2 = _t660;
                      v_h_R_st_d1 = _t661;
                      v_h_R_st_d2 = _t662;
                      v_h_R_st_vb = _t663;
                    }
                    v_hb_R = (v_hb_R + ((v_h_mst * v_o1) * v_h_st_kd));
                }
                if ((((double)((v_h_ase) > (0.5)))) != 0.0) {
                    { double _t664, _t665, _t666, _t667, _t668; F_f_sem(v_hi_R, v_h_R_se_s1, v_h_R_se_s2, v_h_R_se_hq, v_h_R_se_bq, v_h_se_g, v_h_se_R, v_h_chr, 1.0, &_t664, &_t665, &_t666, &_t667, &_t668);
                      v_o1 = _t664;
                      v_h_R_se_s1 = _t665;
                      v_h_R_se_s2 = _t666;
                      v_h_R_se_hq = _t667;
                      v_h_R_se_bq = _t668;
                    }
                    v_hb_R = (v_hb_R + (v_h_mse * v_o1));
                }
                v_e0 = v_hb_R;
                v_e1 = 0.0;
                v_e2 = 0.0;
                v_e3 = 0.0;
                if ((((double)((v_h_xa) > (0.5)))) != 0.0) {
                    { double _t669, _t670, _t671, _t672, _t673; F_f_svf(v_e0, v_h_R_x0_s1, v_h_R_x0_s2, v_h_gx, 0.7071067811865476, &_t669, &_t670, &_t671, &_t672, &_t673);
                      v_eh = _t669;
                      v_eb = _t670;
                      v_el = _t671;
                      v_h_R_x0_s1 = _t672;
                      v_h_R_x0_s2 = _t673;
                    }
                    v_h_R_x0_s1 = fixdenorm(v_h_R_x0_s1);
                    v_h_R_x0_s2 = fixdenorm(v_h_R_x0_s2);
                    v_e1 = v_eh;
                }
                if ((((double)((v_h_xb) > (0.5)))) != 0.0) {
                    { double _t674, _t675, _t676, _t677, _t678; F_f_svf(v_e1, v_h_R_x1_s1, v_h_R_x1_s2, v_h_gx, 0.7071067811865476, &_t674, &_t675, &_t676, &_t677, &_t678);
                      v_eh = _t674;
                      v_eb = _t675;
                      v_el = _t676;
                      v_h_R_x1_s1 = _t677;
                      v_h_R_x1_s2 = _t678;
                    }
                    v_h_R_x1_s1 = fixdenorm(v_h_R_x1_s1);
                    v_h_R_x1_s2 = fixdenorm(v_h_R_x1_s2);
                    v_e2 = v_eh;
                }
                if ((((double)((v_h_xc) > (0.5)))) != 0.0) {
                    { double _t679, _t680, _t681, _t682, _t683; F_f_svf(v_e2, v_h_R_x2_s1, v_h_R_x2_s2, v_h_gx, 0.7071067811865476, &_t679, &_t680, &_t681, &_t682, &_t683);
                      v_eh = _t679;
                      v_eb = _t680;
                      v_el = _t681;
                      v_h_R_x2_s1 = _t682;
                      v_h_R_x2_s2 = _t683;
                    }
                    v_h_R_x2_s1 = fixdenorm(v_h_R_x2_s1);
                    v_h_R_x2_s2 = fixdenorm(v_h_R_x2_s2);
                    v_e3 = v_eh;
                }
                v_wet_R = (((((v_h_w0 * v_e0) + (v_h_w1 * v_e1)) + (v_h_w2 * v_e2)) + (v_h_w3 * v_e3)) * v_h_osc);
                v_hyb_R = (v_lyb_R + (v_h_wet * (v_wet_R - v_lyb_R)));
            }
            v_zb_L = v_hyb_L;
            v_zb_R = v_hyb_R;
        }
    }
    v_y_L = v_za_L;
    v_y_R = v_za_R;
    if ((((double)((v_ovs) > (1.5)))) != 0.0) {
        { double _t684, _t685, _t686, _t687, _t688, _t689, _t690; F_f_ap5(v_zb_L, v_os_L_dna0, v_os_L_dna1, v_os_L_dna2, v_os_L_dna3, v_os_L_dna4, v_os_L_dna5, 0.035979631179546, 0.270744078039831, 0.557994617257913, 0.775098715397111, 0.916958938825425, &_t684, &_t685, &_t686, &_t687, &_t688, &_t689, &_t690);
          v_pa = _t684;
          v_os_L_dna0 = _t685;
          v_os_L_dna1 = _t686;
          v_os_L_dna2 = _t687;
          v_os_L_dna3 = _t688;
          v_os_L_dna4 = _t689;
          v_os_L_dna5 = _t690;
        }
        { double _t691, _t692, _t693, _t694, _t695, _t696, _t697; F_f_ap5(v_za_L, v_os_L_dnb0, v_os_L_dnb1, v_os_L_dnb2, v_os_L_dnb3, v_os_L_dnb4, v_os_L_dnb5, 0.134200951194299, 0.418804850254691, 0.677594451212584, 0.853151529122229, 0.972847950939362, &_t691, &_t692, &_t693, &_t694, &_t695, &_t696, &_t697);
          v_pb = _t691;
          v_os_L_dnb0 = _t692;
          v_os_L_dnb1 = _t693;
          v_os_L_dnb2 = _t694;
          v_os_L_dnb3 = _t695;
          v_os_L_dnb4 = _t696;
          v_os_L_dnb5 = _t697;
        }
        v_y_L = (0.5 * (v_pa + v_pb));
        { double _t698, _t699, _t700, _t701, _t702, _t703, _t704; F_f_ap5(v_zb_R, v_os_R_dna0, v_os_R_dna1, v_os_R_dna2, v_os_R_dna3, v_os_R_dna4, v_os_R_dna5, 0.035979631179546, 0.270744078039831, 0.557994617257913, 0.775098715397111, 0.916958938825425, &_t698, &_t699, &_t700, &_t701, &_t702, &_t703, &_t704);
          v_pa = _t698;
          v_os_R_dna0 = _t699;
          v_os_R_dna1 = _t700;
          v_os_R_dna2 = _t701;
          v_os_R_dna3 = _t702;
          v_os_R_dna4 = _t703;
          v_os_R_dna5 = _t704;
        }
        { double _t705, _t706, _t707, _t708, _t709, _t710, _t711; F_f_ap5(v_za_R, v_os_R_dnb0, v_os_R_dnb1, v_os_R_dnb2, v_os_R_dnb3, v_os_R_dnb4, v_os_R_dnb5, 0.134200951194299, 0.418804850254691, 0.677594451212584, 0.853151529122229, 0.972847950939362, &_t705, &_t706, &_t707, &_t708, &_t709, &_t710, &_t711);
          v_pb = _t705;
          v_os_R_dnb0 = _t706;
          v_os_R_dnb1 = _t707;
          v_os_R_dnb2 = _t708;
          v_os_R_dnb3 = _t709;
          v_os_R_dnb4 = _t710;
          v_os_R_dnb5 = _t711;
        }
        v_y_R = (0.5 * (v_pa + v_pb));
    }
    v_dcr = (1.0 - (((2.0 * M_PI) * 2.0) / v_fs));
    v_og = (Hs_H_og + (v_a_par * (exp((0.11512925465 * gclamp(P_out_db, (-24.0), 12.0))) - Hs_H_og)));
    v_dy_L = ((v_y_L - v_dc_L_x) + (v_dcr * v_dc_L_y));
    v_dc_L_x = v_y_L;
    v_dc_L_y = fixdenorm(v_dy_L);
    v_q_L = (v_dy_L * v_og);
    if ((((double)((P_softclip) > (0.5)))) != 0.0) {
        v_aq = fabs(v_q_L);
        if ((((double)((v_aq) > (0.7)))) != 0.0) {
            v_q_L = (((((double)((v_q_L) > (0.0)))) != 0.0 ? (1.0) : ((-1.0))) * (0.7 + (0.3 * tanh(((v_aq - 0.7) / 0.3)))));
        }
    }
    v_q_L = (v_q_L * v_duck);
    v_q_L = ((((double)((v_q_L) == (v_q_L)))) != 0.0 ? (v_q_L) : (0.0));
    v_dy_R = ((v_y_R - v_dc_R_x) + (v_dcr * v_dc_R_y));
    v_dc_R_x = v_y_R;
    v_dc_R_y = fixdenorm(v_dy_R);
    v_q_R = (v_dy_R * v_og);
    if ((((double)((P_softclip) > (0.5)))) != 0.0) {
        v_aq = fabs(v_q_R);
        if ((((double)((v_aq) > (0.7)))) != 0.0) {
            v_q_R = (((((double)((v_q_R) > (0.0)))) != 0.0 ? (1.0) : ((-1.0))) * (0.7 + (0.3 * tanh(((v_aq - 0.7) / 0.3)))));
        }
    }
    v_q_R = (v_q_R * v_duck);
    v_q_R = ((((double)((v_q_R) == (v_q_R)))) != 0.0 ? (v_q_R) : (0.0));
    *out1 = v_q_L;
    *out2 = v_q_R;
    if ((((double)((v_rst) > (0.5)))) != 0.0) {
        v_l_L_sh_s1a = 0.0;
        v_l_L_sh_s2a = 0.0;
        v_l_L_sh_ba = 0.0;
        v_l_L_sh_s1b = 0.0;
        v_l_L_sh_s2b = 0.0;
        v_l_L_sh_bb = 0.0;
        v_l_L_sh_yp = 0.0;
        v_l_R_sh_s1a = 0.0;
        v_l_R_sh_s2a = 0.0;
        v_l_R_sh_ba = 0.0;
        v_l_R_sh_s1b = 0.0;
        v_l_R_sh_s2b = 0.0;
        v_l_R_sh_bb = 0.0;
        v_l_R_sh_yp = 0.0;
        v_l_L_k3_s1 = 0.0;
        v_l_L_k3_s2 = 0.0;
        v_l_L_k3_s3 = 0.0;
        v_l_L_k3_yp = 0.0;
        v_l_R_k3_s1 = 0.0;
        v_l_R_k3_s2 = 0.0;
        v_l_R_k3_s3 = 0.0;
        v_l_R_k3_yp = 0.0;
        v_l_L_ld_s1 = 0.0;
        v_l_L_ld_s2 = 0.0;
        v_l_L_ld_s3 = 0.0;
        v_l_L_ld_s4 = 0.0;
        v_l_L_ld_p0 = 0.0;
        v_l_L_ld_p1 = 0.0;
        v_l_L_ld_p2 = 0.0;
        v_l_L_ld_p3 = 0.0;
        v_l_L_ld_p4 = 0.0;
        v_l_R_ld_s1 = 0.0;
        v_l_R_ld_s2 = 0.0;
        v_l_R_ld_s3 = 0.0;
        v_l_R_ld_s4 = 0.0;
        v_l_R_ld_p0 = 0.0;
        v_l_R_ld_p1 = 0.0;
        v_l_R_ld_p2 = 0.0;
        v_l_R_ld_p3 = 0.0;
        v_l_R_ld_p4 = 0.0;
        v_l_L_st_s1 = 0.0;
        v_l_L_st_s2 = 0.0;
        v_l_L_st_d1 = 0.0;
        v_l_L_st_d2 = 0.0;
        v_l_L_st_vb = 0.0;
        v_l_R_st_s1 = 0.0;
        v_l_R_st_s2 = 0.0;
        v_l_R_st_d1 = 0.0;
        v_l_R_st_d2 = 0.0;
        v_l_R_st_vb = 0.0;
        v_l_L_se_s1 = 0.0;
        v_l_L_se_s2 = 0.0;
        v_l_L_se_hq = 0.0;
        v_l_L_se_bq = 0.0;
        v_l_R_se_s1 = 0.0;
        v_l_R_se_s2 = 0.0;
        v_l_R_se_hq = 0.0;
        v_l_R_se_bq = 0.0;
        v_l_L_di_s1 = 0.0;
        v_l_L_di_s2 = 0.0;
        v_l_L_di_s3 = 0.0;
        v_l_L_di_s4 = 0.0;
        v_l_L_di_v1 = 0.0;
        v_l_L_di_v2 = 0.0;
        v_l_L_di_v3 = 0.0;
        v_l_L_di_v4 = 0.0;
        v_l_L_di_sf = 0.0;
        v_l_L_di_sc = 0.0;
        v_l_R_di_s1 = 0.0;
        v_l_R_di_s2 = 0.0;
        v_l_R_di_s3 = 0.0;
        v_l_R_di_s4 = 0.0;
        v_l_R_di_v1 = 0.0;
        v_l_R_di_v2 = 0.0;
        v_l_R_di_v3 = 0.0;
        v_l_R_di_v4 = 0.0;
        v_l_R_di_sf = 0.0;
        v_l_R_di_sc = 0.0;
        v_l_L_x0_s1 = 0.0;
        v_l_L_x0_s2 = 0.0;
        v_l_L_x1_s1 = 0.0;
        v_l_L_x1_s2 = 0.0;
        v_l_L_x2_s1 = 0.0;
        v_l_L_x2_s2 = 0.0;
        v_l_R_x0_s1 = 0.0;
        v_l_R_x0_s2 = 0.0;
        v_l_R_x1_s1 = 0.0;
        v_l_R_x1_s2 = 0.0;
        v_l_R_x2_s1 = 0.0;
        v_l_R_x2_s2 = 0.0;
        v_h_L_sh_s1a = 0.0;
        v_h_L_sh_s2a = 0.0;
        v_h_L_sh_ba = 0.0;
        v_h_L_sh_s1b = 0.0;
        v_h_L_sh_s2b = 0.0;
        v_h_L_sh_bb = 0.0;
        v_h_L_sh_yp = 0.0;
        v_h_R_sh_s1a = 0.0;
        v_h_R_sh_s2a = 0.0;
        v_h_R_sh_ba = 0.0;
        v_h_R_sh_s1b = 0.0;
        v_h_R_sh_s2b = 0.0;
        v_h_R_sh_bb = 0.0;
        v_h_R_sh_yp = 0.0;
        v_h_L_k3_s1 = 0.0;
        v_h_L_k3_s2 = 0.0;
        v_h_L_k3_s3 = 0.0;
        v_h_L_k3_yp = 0.0;
        v_h_R_k3_s1 = 0.0;
        v_h_R_k3_s2 = 0.0;
        v_h_R_k3_s3 = 0.0;
        v_h_R_k3_yp = 0.0;
        v_h_L_ld_s1 = 0.0;
        v_h_L_ld_s2 = 0.0;
        v_h_L_ld_s3 = 0.0;
        v_h_L_ld_s4 = 0.0;
        v_h_L_ld_p0 = 0.0;
        v_h_L_ld_p1 = 0.0;
        v_h_L_ld_p2 = 0.0;
        v_h_L_ld_p3 = 0.0;
        v_h_L_ld_p4 = 0.0;
        v_h_R_ld_s1 = 0.0;
        v_h_R_ld_s2 = 0.0;
        v_h_R_ld_s3 = 0.0;
        v_h_R_ld_s4 = 0.0;
        v_h_R_ld_p0 = 0.0;
        v_h_R_ld_p1 = 0.0;
        v_h_R_ld_p2 = 0.0;
        v_h_R_ld_p3 = 0.0;
        v_h_R_ld_p4 = 0.0;
        v_h_L_st_s1 = 0.0;
        v_h_L_st_s2 = 0.0;
        v_h_L_st_d1 = 0.0;
        v_h_L_st_d2 = 0.0;
        v_h_L_st_vb = 0.0;
        v_h_R_st_s1 = 0.0;
        v_h_R_st_s2 = 0.0;
        v_h_R_st_d1 = 0.0;
        v_h_R_st_d2 = 0.0;
        v_h_R_st_vb = 0.0;
        v_h_L_se_s1 = 0.0;
        v_h_L_se_s2 = 0.0;
        v_h_L_se_hq = 0.0;
        v_h_L_se_bq = 0.0;
        v_h_R_se_s1 = 0.0;
        v_h_R_se_s2 = 0.0;
        v_h_R_se_hq = 0.0;
        v_h_R_se_bq = 0.0;
        v_h_L_x0_s1 = 0.0;
        v_h_L_x0_s2 = 0.0;
        v_h_L_x1_s1 = 0.0;
        v_h_L_x1_s2 = 0.0;
        v_h_L_x2_s1 = 0.0;
        v_h_L_x2_s2 = 0.0;
        v_h_R_x0_s1 = 0.0;
        v_h_R_x0_s2 = 0.0;
        v_h_R_x1_s1 = 0.0;
        v_h_R_x1_s2 = 0.0;
        v_h_R_x2_s1 = 0.0;
        v_h_R_x2_s2 = 0.0;
        v_os_L_upa0 = 0.0;
        v_os_L_upa1 = 0.0;
        v_os_L_upa2 = 0.0;
        v_os_L_upa3 = 0.0;
        v_os_L_upa4 = 0.0;
        v_os_L_upa5 = 0.0;
        v_os_L_upb0 = 0.0;
        v_os_L_upb1 = 0.0;
        v_os_L_upb2 = 0.0;
        v_os_L_upb3 = 0.0;
        v_os_L_upb4 = 0.0;
        v_os_L_upb5 = 0.0;
        v_os_L_dna0 = 0.0;
        v_os_L_dna1 = 0.0;
        v_os_L_dna2 = 0.0;
        v_os_L_dna3 = 0.0;
        v_os_L_dna4 = 0.0;
        v_os_L_dna5 = 0.0;
        v_os_L_dnb0 = 0.0;
        v_os_L_dnb1 = 0.0;
        v_os_L_dnb2 = 0.0;
        v_os_L_dnb3 = 0.0;
        v_os_L_dnb4 = 0.0;
        v_os_L_dnb5 = 0.0;
        v_dc_L_x = 0.0;
        v_dc_L_y = 0.0;
        v_os_R_upa0 = 0.0;
        v_os_R_upa1 = 0.0;
        v_os_R_upa2 = 0.0;
        v_os_R_upa3 = 0.0;
        v_os_R_upa4 = 0.0;
        v_os_R_upa5 = 0.0;
        v_os_R_upb0 = 0.0;
        v_os_R_upb1 = 0.0;
        v_os_R_upb2 = 0.0;
        v_os_R_upb3 = 0.0;
        v_os_R_upb4 = 0.0;
        v_os_R_upb5 = 0.0;
        v_os_R_dna0 = 0.0;
        v_os_R_dna1 = 0.0;
        v_os_R_dna2 = 0.0;
        v_os_R_dna3 = 0.0;
        v_os_R_dna4 = 0.0;
        v_os_R_dna5 = 0.0;
        v_os_R_dnb0 = 0.0;
        v_os_R_dnb1 = 0.0;
        v_os_R_dnb2 = 0.0;
        v_os_R_dnb3 = 0.0;
        v_os_R_dnb4 = 0.0;
        v_os_R_dnb5 = 0.0;
        v_dc_R_x = 0.0;
        v_dc_R_y = 0.0;
    }
    Hs_H_l_L_sh_s1a = v_l_L_sh_s1a;
    Hs_H_l_L_sh_s2a = v_l_L_sh_s2a;
    Hs_H_l_L_sh_ba = v_l_L_sh_ba;
    Hs_H_l_L_sh_s1b = v_l_L_sh_s1b;
    Hs_H_l_L_sh_s2b = v_l_L_sh_s2b;
    Hs_H_l_L_sh_bb = v_l_L_sh_bb;
    Hs_H_l_L_sh_yp = v_l_L_sh_yp;
    Hs_H_l_R_sh_s1a = v_l_R_sh_s1a;
    Hs_H_l_R_sh_s2a = v_l_R_sh_s2a;
    Hs_H_l_R_sh_ba = v_l_R_sh_ba;
    Hs_H_l_R_sh_s1b = v_l_R_sh_s1b;
    Hs_H_l_R_sh_s2b = v_l_R_sh_s2b;
    Hs_H_l_R_sh_bb = v_l_R_sh_bb;
    Hs_H_l_R_sh_yp = v_l_R_sh_yp;
    Hs_H_l_L_k3_s1 = v_l_L_k3_s1;
    Hs_H_l_L_k3_s2 = v_l_L_k3_s2;
    Hs_H_l_L_k3_s3 = v_l_L_k3_s3;
    Hs_H_l_L_k3_yp = v_l_L_k3_yp;
    Hs_H_l_R_k3_s1 = v_l_R_k3_s1;
    Hs_H_l_R_k3_s2 = v_l_R_k3_s2;
    Hs_H_l_R_k3_s3 = v_l_R_k3_s3;
    Hs_H_l_R_k3_yp = v_l_R_k3_yp;
    Hs_H_l_L_ld_s1 = v_l_L_ld_s1;
    Hs_H_l_L_ld_s2 = v_l_L_ld_s2;
    Hs_H_l_L_ld_s3 = v_l_L_ld_s3;
    Hs_H_l_L_ld_s4 = v_l_L_ld_s4;
    Hs_H_l_L_ld_p0 = v_l_L_ld_p0;
    Hs_H_l_L_ld_p1 = v_l_L_ld_p1;
    Hs_H_l_L_ld_p2 = v_l_L_ld_p2;
    Hs_H_l_L_ld_p3 = v_l_L_ld_p3;
    Hs_H_l_L_ld_p4 = v_l_L_ld_p4;
    Hs_H_l_R_ld_s1 = v_l_R_ld_s1;
    Hs_H_l_R_ld_s2 = v_l_R_ld_s2;
    Hs_H_l_R_ld_s3 = v_l_R_ld_s3;
    Hs_H_l_R_ld_s4 = v_l_R_ld_s4;
    Hs_H_l_R_ld_p0 = v_l_R_ld_p0;
    Hs_H_l_R_ld_p1 = v_l_R_ld_p1;
    Hs_H_l_R_ld_p2 = v_l_R_ld_p2;
    Hs_H_l_R_ld_p3 = v_l_R_ld_p3;
    Hs_H_l_R_ld_p4 = v_l_R_ld_p4;
    Hs_H_l_L_st_s1 = v_l_L_st_s1;
    Hs_H_l_L_st_s2 = v_l_L_st_s2;
    Hs_H_l_L_st_d1 = v_l_L_st_d1;
    Hs_H_l_L_st_d2 = v_l_L_st_d2;
    Hs_H_l_L_st_vb = v_l_L_st_vb;
    Hs_H_l_R_st_s1 = v_l_R_st_s1;
    Hs_H_l_R_st_s2 = v_l_R_st_s2;
    Hs_H_l_R_st_d1 = v_l_R_st_d1;
    Hs_H_l_R_st_d2 = v_l_R_st_d2;
    Hs_H_l_R_st_vb = v_l_R_st_vb;
    Hs_H_l_L_se_s1 = v_l_L_se_s1;
    Hs_H_l_L_se_s2 = v_l_L_se_s2;
    Hs_H_l_L_se_hq = v_l_L_se_hq;
    Hs_H_l_L_se_bq = v_l_L_se_bq;
    Hs_H_l_R_se_s1 = v_l_R_se_s1;
    Hs_H_l_R_se_s2 = v_l_R_se_s2;
    Hs_H_l_R_se_hq = v_l_R_se_hq;
    Hs_H_l_R_se_bq = v_l_R_se_bq;
    Hs_H_l_L_di_s1 = v_l_L_di_s1;
    Hs_H_l_L_di_s2 = v_l_L_di_s2;
    Hs_H_l_L_di_s3 = v_l_L_di_s3;
    Hs_H_l_L_di_s4 = v_l_L_di_s4;
    Hs_H_l_L_di_v1 = v_l_L_di_v1;
    Hs_H_l_L_di_v2 = v_l_L_di_v2;
    Hs_H_l_L_di_v3 = v_l_L_di_v3;
    Hs_H_l_L_di_v4 = v_l_L_di_v4;
    Hs_H_l_L_di_sf = v_l_L_di_sf;
    Hs_H_l_L_di_sc = v_l_L_di_sc;
    Hs_H_l_R_di_s1 = v_l_R_di_s1;
    Hs_H_l_R_di_s2 = v_l_R_di_s2;
    Hs_H_l_R_di_s3 = v_l_R_di_s3;
    Hs_H_l_R_di_s4 = v_l_R_di_s4;
    Hs_H_l_R_di_v1 = v_l_R_di_v1;
    Hs_H_l_R_di_v2 = v_l_R_di_v2;
    Hs_H_l_R_di_v3 = v_l_R_di_v3;
    Hs_H_l_R_di_v4 = v_l_R_di_v4;
    Hs_H_l_R_di_sf = v_l_R_di_sf;
    Hs_H_l_R_di_sc = v_l_R_di_sc;
    Hs_H_l_L_x0_s1 = v_l_L_x0_s1;
    Hs_H_l_L_x0_s2 = v_l_L_x0_s2;
    Hs_H_l_L_x1_s1 = v_l_L_x1_s1;
    Hs_H_l_L_x1_s2 = v_l_L_x1_s2;
    Hs_H_l_L_x2_s1 = v_l_L_x2_s1;
    Hs_H_l_L_x2_s2 = v_l_L_x2_s2;
    Hs_H_l_R_x0_s1 = v_l_R_x0_s1;
    Hs_H_l_R_x0_s2 = v_l_R_x0_s2;
    Hs_H_l_R_x1_s1 = v_l_R_x1_s1;
    Hs_H_l_R_x1_s2 = v_l_R_x1_s2;
    Hs_H_l_R_x2_s1 = v_l_R_x2_s1;
    Hs_H_l_R_x2_s2 = v_l_R_x2_s2;
    Hs_H_h_L_sh_s1a = v_h_L_sh_s1a;
    Hs_H_h_L_sh_s2a = v_h_L_sh_s2a;
    Hs_H_h_L_sh_ba = v_h_L_sh_ba;
    Hs_H_h_L_sh_s1b = v_h_L_sh_s1b;
    Hs_H_h_L_sh_s2b = v_h_L_sh_s2b;
    Hs_H_h_L_sh_bb = v_h_L_sh_bb;
    Hs_H_h_L_sh_yp = v_h_L_sh_yp;
    Hs_H_h_R_sh_s1a = v_h_R_sh_s1a;
    Hs_H_h_R_sh_s2a = v_h_R_sh_s2a;
    Hs_H_h_R_sh_ba = v_h_R_sh_ba;
    Hs_H_h_R_sh_s1b = v_h_R_sh_s1b;
    Hs_H_h_R_sh_s2b = v_h_R_sh_s2b;
    Hs_H_h_R_sh_bb = v_h_R_sh_bb;
    Hs_H_h_R_sh_yp = v_h_R_sh_yp;
    Hs_H_h_L_k3_s1 = v_h_L_k3_s1;
    Hs_H_h_L_k3_s2 = v_h_L_k3_s2;
    Hs_H_h_L_k3_s3 = v_h_L_k3_s3;
    Hs_H_h_L_k3_yp = v_h_L_k3_yp;
    Hs_H_h_R_k3_s1 = v_h_R_k3_s1;
    Hs_H_h_R_k3_s2 = v_h_R_k3_s2;
    Hs_H_h_R_k3_s3 = v_h_R_k3_s3;
    Hs_H_h_R_k3_yp = v_h_R_k3_yp;
    Hs_H_h_L_ld_s1 = v_h_L_ld_s1;
    Hs_H_h_L_ld_s2 = v_h_L_ld_s2;
    Hs_H_h_L_ld_s3 = v_h_L_ld_s3;
    Hs_H_h_L_ld_s4 = v_h_L_ld_s4;
    Hs_H_h_L_ld_p0 = v_h_L_ld_p0;
    Hs_H_h_L_ld_p1 = v_h_L_ld_p1;
    Hs_H_h_L_ld_p2 = v_h_L_ld_p2;
    Hs_H_h_L_ld_p3 = v_h_L_ld_p3;
    Hs_H_h_L_ld_p4 = v_h_L_ld_p4;
    Hs_H_h_R_ld_s1 = v_h_R_ld_s1;
    Hs_H_h_R_ld_s2 = v_h_R_ld_s2;
    Hs_H_h_R_ld_s3 = v_h_R_ld_s3;
    Hs_H_h_R_ld_s4 = v_h_R_ld_s4;
    Hs_H_h_R_ld_p0 = v_h_R_ld_p0;
    Hs_H_h_R_ld_p1 = v_h_R_ld_p1;
    Hs_H_h_R_ld_p2 = v_h_R_ld_p2;
    Hs_H_h_R_ld_p3 = v_h_R_ld_p3;
    Hs_H_h_R_ld_p4 = v_h_R_ld_p4;
    Hs_H_h_L_st_s1 = v_h_L_st_s1;
    Hs_H_h_L_st_s2 = v_h_L_st_s2;
    Hs_H_h_L_st_d1 = v_h_L_st_d1;
    Hs_H_h_L_st_d2 = v_h_L_st_d2;
    Hs_H_h_L_st_vb = v_h_L_st_vb;
    Hs_H_h_R_st_s1 = v_h_R_st_s1;
    Hs_H_h_R_st_s2 = v_h_R_st_s2;
    Hs_H_h_R_st_d1 = v_h_R_st_d1;
    Hs_H_h_R_st_d2 = v_h_R_st_d2;
    Hs_H_h_R_st_vb = v_h_R_st_vb;
    Hs_H_h_L_se_s1 = v_h_L_se_s1;
    Hs_H_h_L_se_s2 = v_h_L_se_s2;
    Hs_H_h_L_se_hq = v_h_L_se_hq;
    Hs_H_h_L_se_bq = v_h_L_se_bq;
    Hs_H_h_R_se_s1 = v_h_R_se_s1;
    Hs_H_h_R_se_s2 = v_h_R_se_s2;
    Hs_H_h_R_se_hq = v_h_R_se_hq;
    Hs_H_h_R_se_bq = v_h_R_se_bq;
    Hs_H_h_L_x0_s1 = v_h_L_x0_s1;
    Hs_H_h_L_x0_s2 = v_h_L_x0_s2;
    Hs_H_h_L_x1_s1 = v_h_L_x1_s1;
    Hs_H_h_L_x1_s2 = v_h_L_x1_s2;
    Hs_H_h_L_x2_s1 = v_h_L_x2_s1;
    Hs_H_h_L_x2_s2 = v_h_L_x2_s2;
    Hs_H_h_R_x0_s1 = v_h_R_x0_s1;
    Hs_H_h_R_x0_s2 = v_h_R_x0_s2;
    Hs_H_h_R_x1_s1 = v_h_R_x1_s1;
    Hs_H_h_R_x1_s2 = v_h_R_x1_s2;
    Hs_H_h_R_x2_s1 = v_h_R_x2_s1;
    Hs_H_h_R_x2_s2 = v_h_R_x2_s2;
    Hs_H_os_L_upa0 = v_os_L_upa0;
    Hs_H_os_L_upa1 = v_os_L_upa1;
    Hs_H_os_L_upa2 = v_os_L_upa2;
    Hs_H_os_L_upa3 = v_os_L_upa3;
    Hs_H_os_L_upa4 = v_os_L_upa4;
    Hs_H_os_L_upa5 = v_os_L_upa5;
    Hs_H_os_L_upb0 = v_os_L_upb0;
    Hs_H_os_L_upb1 = v_os_L_upb1;
    Hs_H_os_L_upb2 = v_os_L_upb2;
    Hs_H_os_L_upb3 = v_os_L_upb3;
    Hs_H_os_L_upb4 = v_os_L_upb4;
    Hs_H_os_L_upb5 = v_os_L_upb5;
    Hs_H_os_L_dna0 = v_os_L_dna0;
    Hs_H_os_L_dna1 = v_os_L_dna1;
    Hs_H_os_L_dna2 = v_os_L_dna2;
    Hs_H_os_L_dna3 = v_os_L_dna3;
    Hs_H_os_L_dna4 = v_os_L_dna4;
    Hs_H_os_L_dna5 = v_os_L_dna5;
    Hs_H_os_L_dnb0 = v_os_L_dnb0;
    Hs_H_os_L_dnb1 = v_os_L_dnb1;
    Hs_H_os_L_dnb2 = v_os_L_dnb2;
    Hs_H_os_L_dnb3 = v_os_L_dnb3;
    Hs_H_os_L_dnb4 = v_os_L_dnb4;
    Hs_H_os_L_dnb5 = v_os_L_dnb5;
    Hs_H_dc_L_x = v_dc_L_x;
    Hs_H_dc_L_y = v_dc_L_y;
    Hs_H_os_R_upa0 = v_os_R_upa0;
    Hs_H_os_R_upa1 = v_os_R_upa1;
    Hs_H_os_R_upa2 = v_os_R_upa2;
    Hs_H_os_R_upa3 = v_os_R_upa3;
    Hs_H_os_R_upa4 = v_os_R_upa4;
    Hs_H_os_R_upa5 = v_os_R_upa5;
    Hs_H_os_R_upb0 = v_os_R_upb0;
    Hs_H_os_R_upb1 = v_os_R_upb1;
    Hs_H_os_R_upb2 = v_os_R_upb2;
    Hs_H_os_R_upb3 = v_os_R_upb3;
    Hs_H_os_R_upb4 = v_os_R_upb4;
    Hs_H_os_R_upb5 = v_os_R_upb5;
    Hs_H_os_R_dna0 = v_os_R_dna0;
    Hs_H_os_R_dna1 = v_os_R_dna1;
    Hs_H_os_R_dna2 = v_os_R_dna2;
    Hs_H_os_R_dna3 = v_os_R_dna3;
    Hs_H_os_R_dna4 = v_os_R_dna4;
    Hs_H_os_R_dna5 = v_os_R_dna5;
    Hs_H_os_R_dnb0 = v_os_R_dnb0;
    Hs_H_os_R_dnb1 = v_os_R_dnb1;
    Hs_H_os_R_dnb2 = v_os_R_dnb2;
    Hs_H_os_R_dnb3 = v_os_R_dnb3;
    Hs_H_os_R_dnb4 = v_os_R_dnb4;
    Hs_H_os_R_dnb5 = v_os_R_dnb5;
    Hs_H_dc_R_x = v_dc_R_x;
    Hs_H_dc_R_y = v_dc_R_y;
    Hs_H_l_lc = v_l_lc;
    Hs_H_l_rz = v_l_rz;
    Hs_H_l_drv = v_l_drv;
    Hs_H_l_cmp = v_l_cmp;
    Hs_H_l_chr = v_l_chr;
    Hs_H_l_en = v_l_en;
    Hs_H_l_ti = v_l_ti;
    Hs_H_l_w0 = v_l_w0;
    Hs_H_l_w1 = v_l_w1;
    Hs_H_l_w2 = v_l_w2;
    Hs_H_l_w3 = v_l_w3;
    Hs_H_l_cur = v_l_cur;
    Hs_H_l_prev = v_l_prev;
    Hs_H_l_fade = v_l_fade;
    Hs_H_h_lc = v_h_lc;
    Hs_H_h_rz = v_h_rz;
    Hs_H_h_drv = v_h_drv;
    Hs_H_h_cmp = v_h_cmp;
    Hs_H_h_chr = v_h_chr;
    Hs_H_h_en = v_h_en;
    Hs_H_h_ti = v_h_ti;
    Hs_H_h_w0 = v_h_w0;
    Hs_H_h_w1 = v_h_w1;
    Hs_H_h_w2 = v_h_w2;
    Hs_H_h_w3 = v_h_w3;
    Hs_H_h_cur = v_h_cur;
    Hs_H_h_prev = v_h_prev;
    Hs_H_h_fade = v_h_fade;
    Hs_H_cur_order = v_new_order;
    Hs_H_cur_os = v_new_os;
    Hs_H_duck = v_duck;
    Hs_H_og = v_og;
    Hs_H_init = 1.0;
}
void gen_reset(void) {
    Hs_H_l_L_sh_s1a = 0.0;
    Hs_H_l_L_sh_s2a = 0.0;
    Hs_H_l_L_sh_ba = 0.0;
    Hs_H_l_L_sh_s1b = 0.0;
    Hs_H_l_L_sh_s2b = 0.0;
    Hs_H_l_L_sh_bb = 0.0;
    Hs_H_l_L_sh_yp = 0.0;
    Hs_H_l_R_sh_s1a = 0.0;
    Hs_H_l_R_sh_s2a = 0.0;
    Hs_H_l_R_sh_ba = 0.0;
    Hs_H_l_R_sh_s1b = 0.0;
    Hs_H_l_R_sh_s2b = 0.0;
    Hs_H_l_R_sh_bb = 0.0;
    Hs_H_l_R_sh_yp = 0.0;
    Hs_H_l_L_k3_s1 = 0.0;
    Hs_H_l_L_k3_s2 = 0.0;
    Hs_H_l_L_k3_s3 = 0.0;
    Hs_H_l_L_k3_yp = 0.0;
    Hs_H_l_R_k3_s1 = 0.0;
    Hs_H_l_R_k3_s2 = 0.0;
    Hs_H_l_R_k3_s3 = 0.0;
    Hs_H_l_R_k3_yp = 0.0;
    Hs_H_l_L_ld_s1 = 0.0;
    Hs_H_l_L_ld_s2 = 0.0;
    Hs_H_l_L_ld_s3 = 0.0;
    Hs_H_l_L_ld_s4 = 0.0;
    Hs_H_l_L_ld_p0 = 0.0;
    Hs_H_l_L_ld_p1 = 0.0;
    Hs_H_l_L_ld_p2 = 0.0;
    Hs_H_l_L_ld_p3 = 0.0;
    Hs_H_l_L_ld_p4 = 0.0;
    Hs_H_l_R_ld_s1 = 0.0;
    Hs_H_l_R_ld_s2 = 0.0;
    Hs_H_l_R_ld_s3 = 0.0;
    Hs_H_l_R_ld_s4 = 0.0;
    Hs_H_l_R_ld_p0 = 0.0;
    Hs_H_l_R_ld_p1 = 0.0;
    Hs_H_l_R_ld_p2 = 0.0;
    Hs_H_l_R_ld_p3 = 0.0;
    Hs_H_l_R_ld_p4 = 0.0;
    Hs_H_l_L_st_s1 = 0.0;
    Hs_H_l_L_st_s2 = 0.0;
    Hs_H_l_L_st_d1 = 0.0;
    Hs_H_l_L_st_d2 = 0.0;
    Hs_H_l_L_st_vb = 0.0;
    Hs_H_l_R_st_s1 = 0.0;
    Hs_H_l_R_st_s2 = 0.0;
    Hs_H_l_R_st_d1 = 0.0;
    Hs_H_l_R_st_d2 = 0.0;
    Hs_H_l_R_st_vb = 0.0;
    Hs_H_l_L_se_s1 = 0.0;
    Hs_H_l_L_se_s2 = 0.0;
    Hs_H_l_L_se_hq = 0.0;
    Hs_H_l_L_se_bq = 0.0;
    Hs_H_l_R_se_s1 = 0.0;
    Hs_H_l_R_se_s2 = 0.0;
    Hs_H_l_R_se_hq = 0.0;
    Hs_H_l_R_se_bq = 0.0;
    Hs_H_l_L_di_s1 = 0.0;
    Hs_H_l_L_di_s2 = 0.0;
    Hs_H_l_L_di_s3 = 0.0;
    Hs_H_l_L_di_s4 = 0.0;
    Hs_H_l_L_di_v1 = 0.0;
    Hs_H_l_L_di_v2 = 0.0;
    Hs_H_l_L_di_v3 = 0.0;
    Hs_H_l_L_di_v4 = 0.0;
    Hs_H_l_L_di_sf = 0.0;
    Hs_H_l_L_di_sc = 0.0;
    Hs_H_l_R_di_s1 = 0.0;
    Hs_H_l_R_di_s2 = 0.0;
    Hs_H_l_R_di_s3 = 0.0;
    Hs_H_l_R_di_s4 = 0.0;
    Hs_H_l_R_di_v1 = 0.0;
    Hs_H_l_R_di_v2 = 0.0;
    Hs_H_l_R_di_v3 = 0.0;
    Hs_H_l_R_di_v4 = 0.0;
    Hs_H_l_R_di_sf = 0.0;
    Hs_H_l_R_di_sc = 0.0;
    Hs_H_l_L_x0_s1 = 0.0;
    Hs_H_l_L_x0_s2 = 0.0;
    Hs_H_l_L_x1_s1 = 0.0;
    Hs_H_l_L_x1_s2 = 0.0;
    Hs_H_l_L_x2_s1 = 0.0;
    Hs_H_l_L_x2_s2 = 0.0;
    Hs_H_l_R_x0_s1 = 0.0;
    Hs_H_l_R_x0_s2 = 0.0;
    Hs_H_l_R_x1_s1 = 0.0;
    Hs_H_l_R_x1_s2 = 0.0;
    Hs_H_l_R_x2_s1 = 0.0;
    Hs_H_l_R_x2_s2 = 0.0;
    Hs_H_h_L_sh_s1a = 0.0;
    Hs_H_h_L_sh_s2a = 0.0;
    Hs_H_h_L_sh_ba = 0.0;
    Hs_H_h_L_sh_s1b = 0.0;
    Hs_H_h_L_sh_s2b = 0.0;
    Hs_H_h_L_sh_bb = 0.0;
    Hs_H_h_L_sh_yp = 0.0;
    Hs_H_h_R_sh_s1a = 0.0;
    Hs_H_h_R_sh_s2a = 0.0;
    Hs_H_h_R_sh_ba = 0.0;
    Hs_H_h_R_sh_s1b = 0.0;
    Hs_H_h_R_sh_s2b = 0.0;
    Hs_H_h_R_sh_bb = 0.0;
    Hs_H_h_R_sh_yp = 0.0;
    Hs_H_h_L_k3_s1 = 0.0;
    Hs_H_h_L_k3_s2 = 0.0;
    Hs_H_h_L_k3_s3 = 0.0;
    Hs_H_h_L_k3_yp = 0.0;
    Hs_H_h_R_k3_s1 = 0.0;
    Hs_H_h_R_k3_s2 = 0.0;
    Hs_H_h_R_k3_s3 = 0.0;
    Hs_H_h_R_k3_yp = 0.0;
    Hs_H_h_L_ld_s1 = 0.0;
    Hs_H_h_L_ld_s2 = 0.0;
    Hs_H_h_L_ld_s3 = 0.0;
    Hs_H_h_L_ld_s4 = 0.0;
    Hs_H_h_L_ld_p0 = 0.0;
    Hs_H_h_L_ld_p1 = 0.0;
    Hs_H_h_L_ld_p2 = 0.0;
    Hs_H_h_L_ld_p3 = 0.0;
    Hs_H_h_L_ld_p4 = 0.0;
    Hs_H_h_R_ld_s1 = 0.0;
    Hs_H_h_R_ld_s2 = 0.0;
    Hs_H_h_R_ld_s3 = 0.0;
    Hs_H_h_R_ld_s4 = 0.0;
    Hs_H_h_R_ld_p0 = 0.0;
    Hs_H_h_R_ld_p1 = 0.0;
    Hs_H_h_R_ld_p2 = 0.0;
    Hs_H_h_R_ld_p3 = 0.0;
    Hs_H_h_R_ld_p4 = 0.0;
    Hs_H_h_L_st_s1 = 0.0;
    Hs_H_h_L_st_s2 = 0.0;
    Hs_H_h_L_st_d1 = 0.0;
    Hs_H_h_L_st_d2 = 0.0;
    Hs_H_h_L_st_vb = 0.0;
    Hs_H_h_R_st_s1 = 0.0;
    Hs_H_h_R_st_s2 = 0.0;
    Hs_H_h_R_st_d1 = 0.0;
    Hs_H_h_R_st_d2 = 0.0;
    Hs_H_h_R_st_vb = 0.0;
    Hs_H_h_L_se_s1 = 0.0;
    Hs_H_h_L_se_s2 = 0.0;
    Hs_H_h_L_se_hq = 0.0;
    Hs_H_h_L_se_bq = 0.0;
    Hs_H_h_R_se_s1 = 0.0;
    Hs_H_h_R_se_s2 = 0.0;
    Hs_H_h_R_se_hq = 0.0;
    Hs_H_h_R_se_bq = 0.0;
    Hs_H_h_L_x0_s1 = 0.0;
    Hs_H_h_L_x0_s2 = 0.0;
    Hs_H_h_L_x1_s1 = 0.0;
    Hs_H_h_L_x1_s2 = 0.0;
    Hs_H_h_L_x2_s1 = 0.0;
    Hs_H_h_L_x2_s2 = 0.0;
    Hs_H_h_R_x0_s1 = 0.0;
    Hs_H_h_R_x0_s2 = 0.0;
    Hs_H_h_R_x1_s1 = 0.0;
    Hs_H_h_R_x1_s2 = 0.0;
    Hs_H_h_R_x2_s1 = 0.0;
    Hs_H_h_R_x2_s2 = 0.0;
    Hs_H_os_L_upa0 = 0.0;
    Hs_H_os_L_upa1 = 0.0;
    Hs_H_os_L_upa2 = 0.0;
    Hs_H_os_L_upa3 = 0.0;
    Hs_H_os_L_upa4 = 0.0;
    Hs_H_os_L_upa5 = 0.0;
    Hs_H_os_L_upb0 = 0.0;
    Hs_H_os_L_upb1 = 0.0;
    Hs_H_os_L_upb2 = 0.0;
    Hs_H_os_L_upb3 = 0.0;
    Hs_H_os_L_upb4 = 0.0;
    Hs_H_os_L_upb5 = 0.0;
    Hs_H_os_L_dna0 = 0.0;
    Hs_H_os_L_dna1 = 0.0;
    Hs_H_os_L_dna2 = 0.0;
    Hs_H_os_L_dna3 = 0.0;
    Hs_H_os_L_dna4 = 0.0;
    Hs_H_os_L_dna5 = 0.0;
    Hs_H_os_L_dnb0 = 0.0;
    Hs_H_os_L_dnb1 = 0.0;
    Hs_H_os_L_dnb2 = 0.0;
    Hs_H_os_L_dnb3 = 0.0;
    Hs_H_os_L_dnb4 = 0.0;
    Hs_H_os_L_dnb5 = 0.0;
    Hs_H_dc_L_x = 0.0;
    Hs_H_dc_L_y = 0.0;
    Hs_H_os_R_upa0 = 0.0;
    Hs_H_os_R_upa1 = 0.0;
    Hs_H_os_R_upa2 = 0.0;
    Hs_H_os_R_upa3 = 0.0;
    Hs_H_os_R_upa4 = 0.0;
    Hs_H_os_R_upa5 = 0.0;
    Hs_H_os_R_upb0 = 0.0;
    Hs_H_os_R_upb1 = 0.0;
    Hs_H_os_R_upb2 = 0.0;
    Hs_H_os_R_upb3 = 0.0;
    Hs_H_os_R_upb4 = 0.0;
    Hs_H_os_R_upb5 = 0.0;
    Hs_H_os_R_dna0 = 0.0;
    Hs_H_os_R_dna1 = 0.0;
    Hs_H_os_R_dna2 = 0.0;
    Hs_H_os_R_dna3 = 0.0;
    Hs_H_os_R_dna4 = 0.0;
    Hs_H_os_R_dna5 = 0.0;
    Hs_H_os_R_dnb0 = 0.0;
    Hs_H_os_R_dnb1 = 0.0;
    Hs_H_os_R_dnb2 = 0.0;
    Hs_H_os_R_dnb3 = 0.0;
    Hs_H_os_R_dnb4 = 0.0;
    Hs_H_os_R_dnb5 = 0.0;
    Hs_H_dc_R_x = 0.0;
    Hs_H_dc_R_y = 0.0;
    Hs_H_l_lc = 14.287712379549449;
    Hs_H_l_rz = 0.0;
    Hs_H_l_drv = 0.0;
    Hs_H_l_cmp = 1.0;
    Hs_H_l_chr = 0.0;
    Hs_H_l_en = 1.0;
    Hs_H_l_ti = 1.0;
    Hs_H_l_w0 = 1.0;
    Hs_H_l_w1 = 0.0;
    Hs_H_l_w2 = 0.0;
    Hs_H_l_w3 = 0.0;
    Hs_H_l_cur = 2.0;
    Hs_H_l_prev = 2.0;
    Hs_H_l_fade = 1.0;
    Hs_H_h_lc = 4.321928094887363;
    Hs_H_h_rz = 0.0;
    Hs_H_h_drv = 0.0;
    Hs_H_h_cmp = 1.0;
    Hs_H_h_chr = 0.0;
    Hs_H_h_en = 1.0;
    Hs_H_h_ti = 0.0;
    Hs_H_h_w0 = 1.0;
    Hs_H_h_w1 = 0.0;
    Hs_H_h_w2 = 0.0;
    Hs_H_h_w3 = 0.0;
    Hs_H_h_cur = 1.0;
    Hs_H_h_prev = 1.0;
    Hs_H_h_fade = 1.0;
    Hs_H_cur_order = 0.0;
    Hs_H_cur_os = 0.0;
    Hs_H_duck = 1.0;
    Hs_H_og = 1.0;
    Hs_H_init = 0.0;
    P_l_on = 1.0;
    P_l_model = 2.0;
    P_l_cut = 20000.0;
    P_l_res = 0.0;
    P_l_slope = 1.0;
    P_l_drive = 0.0;
    P_l_comp = 100.0;
    P_l_char = 0.0;
    P_h_on = 1.0;
    P_h_model = 1.0;
    P_h_cut = 20.0;
    P_h_res = 0.0;
    P_h_slope = 0.0;
    P_h_drive = 0.0;
    P_h_comp = 100.0;
    P_h_char = 0.0;
    P_order_sel = 0.0;
    P_ovs_sel = 0.0;
    P_out_db = 0.0;
    P_softclip = 1.0;
}
int gen_set_param(const char* n, double v) {
    if (!strcmp(n, "l_on")) { P_l_on = gclamp(v, 0.0, 1.0); return 0; }
    if (!strcmp(n, "l_model")) { P_l_model = gclamp(v, 0.0, 5.0); return 0; }
    if (!strcmp(n, "l_cut")) { P_l_cut = gclamp(v, 20.0, 20000.0); return 0; }
    if (!strcmp(n, "l_res")) { P_l_res = gclamp(v, 0.0, 100.0); return 0; }
    if (!strcmp(n, "l_slope")) { P_l_slope = gclamp(v, 0.0, 3.0); return 0; }
    if (!strcmp(n, "l_drive")) { P_l_drive = gclamp(v, 0.0, 100.0); return 0; }
    if (!strcmp(n, "l_comp")) { P_l_comp = gclamp(v, 0.0, 100.0); return 0; }
    if (!strcmp(n, "l_char")) { P_l_char = gclamp(v, 0.0, 100.0); return 0; }
    if (!strcmp(n, "h_on")) { P_h_on = gclamp(v, 0.0, 1.0); return 0; }
    if (!strcmp(n, "h_model")) { P_h_model = gclamp(v, 0.0, 4.0); return 0; }
    if (!strcmp(n, "h_cut")) { P_h_cut = gclamp(v, 20.0, 2000.0); return 0; }
    if (!strcmp(n, "h_res")) { P_h_res = gclamp(v, 0.0, 100.0); return 0; }
    if (!strcmp(n, "h_slope")) { P_h_slope = gclamp(v, 0.0, 3.0); return 0; }
    if (!strcmp(n, "h_drive")) { P_h_drive = gclamp(v, 0.0, 100.0); return 0; }
    if (!strcmp(n, "h_comp")) { P_h_comp = gclamp(v, 0.0, 100.0); return 0; }
    if (!strcmp(n, "h_char")) { P_h_char = gclamp(v, 0.0, 100.0); return 0; }
    if (!strcmp(n, "order_sel")) { P_order_sel = gclamp(v, 0.0, 1.0); return 0; }
    if (!strcmp(n, "ovs_sel")) { P_ovs_sel = gclamp(v, 0.0, 1.0); return 0; }
    if (!strcmp(n, "out_db")) { P_out_db = gclamp(v, -24.0, 12.0); return 0; }
    if (!strcmp(n, "softclip")) { P_softclip = gclamp(v, 0.0, 1.0); return 0; }
    return -1;
}
void gen_set_sr(double sr) { g_sr = sr; }
