// Synthetic response orchestration only: every physical prediction is compiled
// SDK.
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <irred/curved_flrw.hpp>
#include <irred/decaying_matter.hpp>
#include <irred/dgp_growth.hpp>
#include <irred/hernquist_sphere.hpp>
#include <irred/nfw_halo.hpp>
#include <irred/quintessence.hpp>
#include <string>
#include <vector>
#ifndef CAMPAIGN_BUILD_ID
#error actual production build identity required
#endif
#ifndef CAMPAIGN_REQUEST_SHA
#error frozen request identity required
#endif
using S = irred::numerics::Status;
namespace {
bool first_case = true, first_value = true;
void number(long double x) {
  if (std::isfinite(x))
    std::cout << x;
  else
    std::cout << "null";
}
void field(const char *key, S status, long double value,
           long double error = 0) {
  if (!first_value)
    std::cout << ',';
  first_value = false;
  std::cout << '"' << key << "\":{\"status\":" << int(status) << ",\"value\":";
  if (status == S::ok)
    number(value);
  else
    std::cout << "null";
  std::cout << ",\"absolute_error_estimate\":";
  number(error);
  std::cout << '}';
}
template <class V> void optional_field(const char *key, const V &v) {
  field(key, v.status, v.value ? *v.value : 0, v.absolute_error_estimate);
}
void scalar_field(const char *key, const irred::numerics::ScalarResult &v) {
  field(key, v.status, v.value, v.error_estimate);
}
void begin(const char *family, std::string id, const std::string_view model,
           bool refined, const std::string &parameters, S status) {
  if (!first_case)
    std::cout << ',';
  first_case = false;
  std::cout << "{\"family\":\"" << family << "\",\"id\":\"" << id
            << "\",\"model_id\":\"" << model << "\",\"resolution\":\""
            << (refined ? "refined" : "default")
            << "\",\"parameters\":" << parameters
            << ",\"native_status\":" << int(status) << ",\"rows\":[";
}
void row(double coordinate, S status, size_t work, bool comma) {
  if (comma)
    std::cout << ',';
  std::cout << "{\"coordinate\":" << coordinate
            << ",\"native_status\":" << int(status) << ",\"work\":" << work
            << ",\"values\":{";
  first_value = true;
}
void endrow() { std::cout << "}}"; }
void endcase() { std::cout << "]}"; }
std::string value(double x) { return std::to_string(x); }
void control(const char *id, bool passed, bool comma, S actual = S::ok) {
  if (comma)
    std::cout << ',';
  std::cout << "{\"id\":\"" << id
            << "\",\"passed\":" << (passed ? "true" : "false")
            << ",\"actual_native_status\":" << int(actual) << '}';
}
} // namespace
int main(int argc, char **argv) {
  if (argc != 2 ||
      (std::string(argv[1]) != "quick" && std::string(argv[1]) != "broader"))
    return 2;
  const bool broader = std::string(argv[1]) == "broader";
  std::cout << std::setprecision(21);
  const std::vector<double> a =
      broader ? std::vector<double>{.1, .2, .3, .4, .5, .6, .7, .8, .9, 1}
              : std::vector<double>{.25, .5, .75, 1};
  const std::vector<double> da =
      broader ? std::vector<double>{.1, .15, .2, .3, .4, .5, .6, .7, .8, .9, 1}
              : std::vector<double>{.1, .2, .5, 1};
  const std::vector<double> z =
      broader
          ? std::vector<double>{0, .1, .2, .3, .4, .5, .75, 1, 1.5, 2, 2.5, 3}
          : std::vector<double>{0, .1, .5, 1, 2, 3};
  const std::vector<double> radii =
      broader ? std::vector<double>{.01, .02, .03, .05, .075, .1, .15,
                                    .2,  .3,  .5,  .75, 1,    2}
              : std::vector<double>{.02, .05, .1, .2, .5, 1};
  const std::vector<double> ratios =
      broader
          ? std::vector<double>{.1, .2, .3, .5, .75, 1, 1.5, 2, 3, 5, 7.5, 10}
          : std::vector<double>{.1, .5, 1, 2, 5, 10};
  std::cout
      << "{\"schema\":\"compiled-native-model-campaign/v1\",\"build_id\":\""
      << CAMPAIGN_BUILD_ID << "\",\"request_sha256\":\"" << CAMPAIGN_REQUEST_SHA
      << "\",\"profile\":\"" << argv[1]
      << "\",\"scientific_role\":\"synthetic_and_conditional_predictions\","
         "\"observations\":null,\"inference\":null,\"cases\":[";
  for (bool refined : {false, true}) {
    for (double lambda : {0., .4, .8}) {
      irred::cosmology::ExponentialQuintessence spec{lambda, 70, 0, .7, 0};
      irred::cosmology::QuintessencePolicy p;
      if (refined) {
        p.relative_tolerance = 1e-11;
        p.absolute_tolerance = 1e-12;
      }
      auto out =
          irred::cosmology::prepare_quintessence(spec).evaluate(a, true, p);
      begin("quintessence", "lambda-" + value(lambda),
            irred::cosmology::quintessence_model_id, refined,
            "{\"lambda\":" + value(lambda) +
                ",\"h_anchor_km_s_mpc\":70,\"signed_kinetic_fraction_root\":0,"
                "\"potential_fraction\":0.7,\"radiation_fraction\":0,\"anchor_"
                "a\":1}",
            out.status);
      for (size_t i = 0; i < out.rows.size(); ++i) {
        const auto &r = out.rows[i];
        row(r.scale_factor, r.status, r.callbacks, i);
        optional_field("E", r.e);
        optional_field("H_km_s_Mpc", r.h_km_s_mpc);
        optional_field("w_phi", r.w_phi);
        optional_field("Omega_phi", r.omega_phi);
        optional_field("Omega_m", r.omega_m);
        optional_field("Omega_r", r.omega_r);
        optional_field("DM_Mpc", r.dm_mpc);
        optional_field("DL_Mpc", r.dl_mpc);
        field("constraint_residual", S::ok, r.constraint_residual);
        endrow();
      }
      endcase();
    }
    for (double om : {.2, .3, .4, 1.}) {
      auto model = irred::cosmology::prepare_dgp_growth({om, 70});
      irred::cosmology::DGPPolicy p;
      if (refined)
        p.relative_tolerance = 1e-10;
      auto out = model.evaluate(a, 63, p);
      begin("dgp", "omega-" + value(om), irred::cosmology::dgp_growth_id,
            refined, "{\"omega_m0\":" + value(om) + ",\"h0_km_s_mpc\":70}",
            out.status);
      for (size_t i = 0; i < out.rows.size(); ++i) {
        const auto &r = out.rows[i];
        row(r.scale_factor, out.status, r.callbacks, i);
        optional_field("E", r.e);
        optional_field("H_km_s_Mpc", r.h);
        optional_field("Omega_m", r.omega_m);
        optional_field("mu", r.mu);
        optional_field("D", r.d);
        optional_field("f", r.f);
        endrow();
      }
      endcase();
    }
    unsigned halo_id = 0;
    for (double rho : {5e14, 1e15, 2e15})
      for (double rs : {.1, .2, .4}) {
        irred::lensing::NFWHalo halo{rho, rs};
        double tol = refined ? 1e-12 : 1e-10;
        begin("nfw", "halo-" + std::to_string(halo_id++),
              irred::lensing::nfw_halo_id, refined,
              "{\"rho_s_msun_mpc3\":" + std::to_string(rho) +
                  ",\"radius_s_mpc\":" + value(rs) +
                  ",\"sigma_critical_msun_mpc2\":3e15,\"lens_distance_mpc\":"
                  "1000}",
              S::ok);
        for (size_t i = 0; i < radii.size(); ++i) {
          const double radius = radii[i];
          const auto mass =
              irred::lensing::nfw_enclosed_mass(halo, radius, tol);
          const auto proj = irred::lensing::nfw_projection(halo, radius, tol);
          const auto lens =
              irred::lensing::nfw_lens(halo, radius, 3e15, 1000, tol);
          row(radius, proj.status, 0, i);
          scalar_field("mass_enclosed_Msun", mass);
          scalar_field("Sigma_Msun_Mpc2", proj.surface_density);
          scalar_field("mean_Sigma_Msun_Mpc2", proj.mean_surface_density);
          scalar_field("Delta_Sigma_Msun_Mpc2", proj.excess_surface_density);
          scalar_field("kappa", lens.convergence);
          scalar_field("gamma_t", lens.tangential_shear);
          scalar_field("alpha_radians", lens.deflection_radians);
          endrow();
        }
        endcase();
      }
    for (double rate : {0., .1, .5, 1.}) {
      irred::cosmology::DecayingMatterModel spec{.1, 1e-16, .1,  .8,
                                                 .1, 0,     rate};
      irred::cosmology::DecayingMatterPolicy p;
      if (refined) {
        p.relative_tolerance = 1e-11;
        p.absolute_tolerance = 1e-13;
      }
      auto out = irred::cosmology::evolve_decaying_matter(spec, da, p);
      begin("decaying-matter", "rate-" + value(rate),
            irred::cosmology::decaying_matter_model_id, refined,
            "{\"initial_scale_factor\":0.1,\"initial_hubble_per_second\":1e-16,"
            "\"stable_matter_fraction\":0.1,\"parent_fraction\":0.8,\"daughter_"
            "radiation_fraction\":0.1,\"lambda_fraction\":0,\"decay_rate_over_"
            "initial_hubble\":" +
                value(rate) + "}",
            out.status);
      for (size_t i = 0; i < out.rows.size(); ++i) {
        const auto &r = out.rows[i];
        row(r.scale_factor, out.status, out.rhs_evaluations, i);
        field("E_over_initial", out.status, r.expansion_over_initial_hubble);
        field("H_per_second", out.status, r.hubble_per_second);
        field("elapsed_initial_hubble_time", out.status,
              r.elapsed_initial_hubble_time,
              r.elapsed_initial_hubble_time_estimate);
        field("elapsed_seconds", out.status, r.elapsed_seconds);
        field("Omega_stable", out.status, r.stable_matter_fraction);
        field("Omega_parent", out.status, r.parent_fraction);
        field("Omega_daughter", out.status, r.daughter_radiation_fraction);
        field("w_total", out.status, r.total_equation_of_state);
        field("deceleration", out.status, r.deceleration);
        field("transfer_over_Hrho", out.status,
              r.transfer_over_hubble_total_density);
        field("continuity_residual", out.status, r.continuity_residual);
        endrow();
      }
      endcase();
    }
    for (double ol : {.6, .7, .8}) {
      irred::cosmology::CurvedFLRW model({70, .3, 0, ol});
      irred::cosmology::CurvedFLRWPolicy p;
      if (refined) {
        p.relative_tolerance = 1e-11;
        p.absolute_tolerance_mpc = 1e-9;
      }
      auto out = model.evaluate(z, p);
      begin("curved-flrw", "lambda-" + value(ol),
            irred::cosmology::curved_flrw_id, refined,
            "{\"h0_km_s_mpc\":70,\"omega_m\":0.3,\"omega_r\":0,\"omega_"
            "lambda\":" +
                value(ol) + ",\"omega_k\":" + value(model.omega_k()) + "}",
            out.status);
      for (size_t i = 0; i < out.rows.size(); ++i) {
        const auto &r = out.rows[i];
        row(r.redshift, r.status, r.callbacks, i);
        field("E", r.status, r.e, r.e_error_estimate);
        field("H_km_s_Mpc", r.status, r.h_km_s_mpc,
              r.h_error_estimate_km_s_mpc);
        field("DC_Mpc", r.status, r.radial_mpc, r.radial_error_estimate_mpc);
        field("DM_Mpc", r.status, r.transverse_mpc,
              r.transverse_error_estimate_mpc);
        field("DA_Mpc", r.status, r.angular_mpc);
        field("DL_Mpc", r.status, r.luminosity_mpc);
        endrow();
      }
      endcase();
    }
    unsigned sphere_id = 0;
    for (double mass : {1e40, 1e41})
      for (double scale : {1e19, 3e19}) {
        irred::gravity::HernquistSphere model{mass, scale, 6.67430e-11};
        begin("hernquist", "sphere-" + std::to_string(sphere_id++),
              irred::gravity::hernquist_sphere_id, refined,
              "{\"total_mass_kg\":" + std::to_string(mass) +
                  ",\"scale_radius_metres\":" + std::to_string(scale) +
                  ",\"gravitational_coupling_m3_kg_s2\":6.67430e-11}",
              S::ok);
        for (size_t i = 0; i < ratios.size(); ++i) {
          const auto r = irred::gravity::evaluate_hernquist_sphere(
              model, ratios[i] * scale, refined ? 1e-13 : 1e-12);
          row(ratios[i] * scale, r.status, 0, i);
          scalar_field("mass_enclosed_kg", r.enclosed_mass_kg);
          scalar_field("density_kg_m3", r.density_kg_m3);
          scalar_field("potential_m2_s2", r.potential_m2_s2);
          scalar_field("radial_acceleration_m_s2",
                       r.inward_radial_acceleration_m_s2);
          scalar_field("circular_speed_squared_m2_s2",
                       r.circular_speed_squared_m2_s2);
          scalar_field("tidal_radial_s2", r.potential_radial_curvature_s2);
          scalar_field("tidal_tangential_s2",
                       r.potential_tangential_curvature_s2);
          endrow();
        }
        endcase();
      }
  }
  std::cout << "],\"controls\":[";
  const std::array<double, 1> now{1};
  const auto eds =
      irred::cosmology::prepare_dgp_growth({1, 70}).evaluate(now, 63);
  control("DGP infinite-rc EdS endpoint",
          eds.status == S::ok && eds.rows[0].d.value == 1 &&
              eds.rows[0].f.value == 1,
          false);
  const auto bad = irred::cosmology::prepare_dgp_growth({-.1, 70});
  control("DGP unsupported fraction refused", bad.status() == S::outside_domain,
          true, bad.status());
  const auto singular =
      irred::gravity::evaluate_hernquist_sphere({1e40, 1e19, 6.67430e-11}, 0);
  control("Hernquist origin partial singular refusal",
          singular.status == S::singular &&
              singular.enclosed_mass_kg.status == S::ok &&
              singular.enclosed_mass_kg.value == 0 &&
              singular.density_kg_m3.status == S::singular,
          true, singular.status);
  auto q = irred::cosmology::prepare_quintessence({0, 70, 0, .7, 0})
               .evaluate(std::array<double, 1>{.5}, true);
  auto c = irred::cosmology::CurvedFLRW({70, .3, 0, .7})
               .evaluate(std::array<double, 1>{1});
  const bool compatible =
      q.status == S::ok && c.status == S::ok && q.rows[0].e.value &&
      q.rows[0].dm_mpc.value &&
      std::abs(*q.rows[0].e.value - c.rows[0].e) < 1e-8 &&
      std::abs(*q.rows[0].dm_mpc.value - c.rows[0].transverse_mpc) < 1e-4;
  control("lambda-zero flat geometry inter-consumer reference", compatible,
          true);
  std::cout << "],\"gates\":{\"inference\":\"not_performed\","
               "\"interpretation\":\"synthetic and conditional model responses "
               "only\",\"certified_error_bound\":null}}\n";
}
