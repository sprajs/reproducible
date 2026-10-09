// Experiment orchestration: physical predictions are production installed SDK
// calls.
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <irred/chaplygin.hpp>
#include <irred/curved_flrw.hpp>
#include <irred/plummer_population.hpp>
#include <sstream>
#include <string>
#include <vector>
#ifndef CAMPAIGN_BUILD_ID
#error production SDK build identity required
#endif
#ifndef CAMPAIGN_REQUEST_SHA
#error frozen request identity required
#endif
using S = irred::numerics::Status;
namespace {
bool first_case = true, first_value = true, first_control = true;
void number(long double v) {
  if (std::isfinite(v))
    std::cout << v;
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
void scalar(const char *key, const irred::numerics::ScalarResult &x) {
  field(key, x.status, x.value, x.error_estimate);
}
void begin(const char *family, unsigned id, std::string_view model,
           bool refined, const std::string &pars, S status) {
  if (!first_case)
    std::cout << ',';
  first_case = false;
  std::cout << "{\"family\":\"" << family << "\",\"id\":" << id
            << ",\"model_id\":\"" << model << "\",\"resolution\":\""
            << (refined ? "refined" : "default") << "\",\"parameters\":" << pars
            << ",\"native_status\":" << int(status);
}
void values() {
  std::cout << ",\"values\":{";
  first_value = true;
}
std::string cgpars(double as, double alpha) {
  std::ostringstream s;
  s << std::setprecision(17)
    << "{\"H0_km_s_Mpc\":70,\"ordinary_matter_fraction\":0.3,\"radiation_"
       "fraction\":0,\"a_s\":"
    << as << ",\"alpha\":" << alpha << '}';
  return s.str();
}
std::string poppars(double m, double b) {
  std::ostringstream s;
  s << std::setprecision(17) << "{\"M_kg\":" << m << ",\"b_m\":" << b
    << ",\"supplied_G_m3_kg_s2\":6.67430e-11}";
  return s.str();
}
void control(const std::string &id, bool pass, S status = S::ok,
             long double difference = 0) {
  if (!first_control)
    std::cout << ',';
  first_control = false;
  std::cout << "{\"id\":\"" << id
            << "\",\"passed\":" << (pass ? "true" : "false")
            << ",\"native_status\":" << int(status)
            << ",\"maximum_absolute_E_difference\":";
  number(difference);
  std::cout << '}';
}
} // namespace
int main(int argc, char **argv) {
  if (argc != 2 ||
      (std::string(argv[1]) != "quick" && std::string(argv[1]) != "broader"))
    return 2;
  bool broader = std::string(argv[1]) == "broader";
  const std::vector<double> a =
      broader
          ? std::vector<double>{1, .8, .6, .5, .4, .3, .2, .15, .1, .075, .05}
          : std::vector<double>{1, .5, .2, .1, .05};
  const std::vector<double> radius =
      broader ? std::vector<double>{0, .05, .1, .2, .3, .5,  .75,
                                    1, 1.5, 2,  3,  5,  7.5, 10}
              : std::vector<double>{0, .1, .5, 1, 2, 5, 10};
  const std::vector<double> q =
      broader ? std::vector<double>{0,   .1,  .25, .4,  .5, .6,
                                    .75, .85, .9,  .95, 1,  1.001}
              : std::vector<double>{0, .25, .5, .75, .9, 1, 1.001};
  std::cout
      << std::setprecision(21)
      << "{\"schema\":\"compiled-native-fluid-population/v1\",\"profile\":\""
      << argv[1] << "\",\"build_id\":\"" << CAMPAIGN_BUILD_ID
      << "\",\"request_sha256\":\"" << CAMPAIGN_REQUEST_SHA
      << "\",\"observations\":null,\"inference\":null,\"cases\":[";
  bool outside_pass = true;
  std::size_t outside_count = 0, boundary_count = 0, ambiguous_count = 0;
  for (bool refined : {false, true}) {
    irred::cosmology::ChaplyginPolicy policy;
    policy.relative_tolerance = refined ? 1e-11 : 1e-9;
    policy.absolute_distance_tolerance_mpc = refined ? 1e-9 : 1e-7;
    unsigned id = 0;
    for (double as : {0., .3, .7, 1.})
      for (double alpha : {0., .5, 1.}) {
        auto out = irred::cosmology::evolve_chaplygin(
            {70, .3, 0, as, alpha}, a, irred::cosmology::chaplygin_distances,
            policy);
        begin("chaplygin", id++, irred::cosmology::chaplygin_model_id, refined,
              cgpars(as, alpha), out.status);
        std::cout << ",\"callbacks\":" << out.callbacks << ",\"rows\":[";
        for (std::size_t i = 0; i < out.rows.size(); ++i) {
          const auto &r = out.rows[i];
          if (i)
            std::cout << ',';
          std::cout << "{\"coordinate\":" << r.scale_factor
                    << ",\"native_status\":" << int(out.status);
          values();
          field("E", out.status, r.expansion_over_anchor_hubble,
                r.background_relative_estimate *
                    r.expansion_over_anchor_hubble);
          field("H_km_s_Mpc", out.status, r.hubble_km_s_mpc,
                r.background_relative_estimate * r.hubble_km_s_mpc);
          field("rho_fluid_over_anchor", out.status,
                r.fluid_density_over_anchor_fluid_density);
          field("Omega_ordinary", out.status, r.ordinary_matter_fraction);
          field("Omega_radiation", out.status, r.radiation_fraction);
          field("Omega_fluid", out.status, r.fluid_fraction);
          field("w_fluid", out.status, r.fluid_equation_of_state);
          field("one_plus_w_fluid", out.status,
                r.fluid_one_plus_equation_of_state);
          field("formal_dp_de", out.status, r.fluid_barotropic_slope);
          field("w_total", out.status, r.total_equation_of_state);
          field("deceleration", out.status, r.deceleration);
          if (r.distances) {
            field("DC_Mpc", out.status, r.distances->comoving_mpc,
                  r.distances->comoving_estimate_mpc);
            field("DA_Mpc", out.status, r.distances->angular_diameter_mpc,
                  r.distances->angular_diameter_estimate_mpc);
            field("DL_Mpc", out.status, r.distances->luminosity_mpc,
                  r.distances->luminosity_estimate_mpc);
          }
          std::cout << "}}";
        }
        std::cout << "]}";
      }
    id = 0;
    for (double mass : {1e40, 1e41})
      for (double scale : {1e19, 3e19}) {
        std::vector<double> physical;
        for (double ratio : radius)
          physical.push_back(ratio * scale);
        irred::gravity::PlummerPopulationPreparationPolicy prep;
        prep.relative_tolerance = refined ? 1e-12 : 1e-10;
        auto population = irred::gravity::prepare_plummer_population(
            {mass, scale, 6.67430e-11}, physical, prep);
        std::vector<irred::gravity::PlummerVelocityRequest> queries;
        if (population.status() == S::ok)
          for (std::size_t i = 0; i < radius.size(); ++i)
            for (double speed_ratio : q)
              queries.push_back(
                  {i,
                   speed_ratio * population.radii()[i].escape_speed_m_s.value});
        irred::gravity::PlummerPopulationEvaluationPolicy eval;
        eval.relative_tolerance = refined ? 1e-12 : 1e-10;
        auto batch = population.evaluate(queries, eval);
        begin("plummer_population", id++, irred::gravity::plummer_population_id,
              refined, poppars(mass, scale), population.status());
        std::cout << ",\"batch_native_status\":" << int(batch.status)
                  << ",\"native_preparation_evaluations\":"
                  << population.native_evaluations()
                  << ",\"velocity_evaluations\":" << batch.velocity_evaluations
                  << ",\"radius_states\":[";
        for (std::size_t i = 0; i < population.radii().size(); ++i) {
          const auto &r = population.radii()[i];
          if (i)
            std::cout << ',';
          std::cout << "{\"coordinate\":" << radius[i]
                    << ",\"radius_m\":" << r.radius_metres
                    << ",\"native_status\":" << int(r.status);
          values();
          scalar("density_kg_m3", r.density_kg_m3);
          scalar("Psi_m2_s2", r.relative_potential_m2_s2);
          scalar("enclosed_mass_kg", r.enclosed_mass_kg);
          scalar("projected_surface_density_kg_m2",
                 r.projected_surface_density_kg_m2);
          scalar("escape_speed_m_s", r.escape_speed_m_s);
          scalar("one_axis_variance_m2_s2", r.one_axis_variance_m2_s2);
          scalar("projected_los_variance_m2_s2",
                 r.projected_los_variance_m2_s2);
          std::cout << "}}";
        }
        std::cout << "],\"rows\":[";
        for (std::size_t i = 0; i < batch.rows.size(); ++i) {
          const auto &r = batch.rows[i];
          const auto ri = r.request.radius_index;
          const double qi = q[i % q.size()];
          if (i)
            std::cout << ',';
          std::cout << "{\"coordinate\":{\"radius_index\":" << ri
                    << ",\"radius_over_scale\":" << radius[ri]
                    << ",\"speed_over_native_escape\":" << qi
                    << "},\"speed_m_s\":" << r.request.speed_m_s
                    << ",\"native_status\":" << int(r.status)
                    << ",\"support\":" << int(r.support)
                    << ",\"binding_energy_m2_s2\":";
          number(r.binding_energy_m2_s2);
          std::cout << ",\"binding_energy_absolute_error_m2_s2\":";
          number(r.binding_energy_absolute_error_m2_s2);
          values();
          scalar("DF_kg_s3_m6", r.distribution_function_kg_s3_m6);
          scalar("vector_PDF_s3_m3", r.vector_velocity_density_s3_m3);
          scalar("speed_PDF_s_m", r.speed_density_s_m);
          std::cout << "}}";
          if (qi == 1) {
            ++boundary_count;
            if (r.support == irred::gravity::PlummerEnergySupport::ambiguous)
              ++ambiguous_count;
          }
          if (qi > 1) {
            ++outside_count;
            outside_pass =
                outside_pass && r.status == S::ok &&
                r.support == irred::gravity::PlummerEnergySupport::outside &&
                r.binding_energy_m2_s2 +
                        r.binding_energy_absolute_error_m2_s2 <=
                    0 &&
                r.distribution_function_kg_s3_m6.value == 0 &&
                r.vector_velocity_density_s3_m3.value == 0 &&
                r.speed_density_s_m.value == 0;
          }
        }
        std::cout << "]}";
      }
  }
  std::cout << "],\"controls\":[";
  unsigned id = 0;
  for (double as : {0., .3, .7, 1.})
    for (double alpha : {0., .5, 1.})
      if (alpha == 0 || as == 0 || as == 1) {
        irred::cosmology::ChaplyginPolicy p;
        p.relative_tolerance = 1e-11;
        p.absolute_distance_tolerance_mpc = 1e-9;
        auto cg = irred::cosmology::evolve_chaplygin(
            {70, .3, 0, as, alpha}, a, irred::cosmology::chaplygin_distances,
            p);
        std::vector<double> z;
        for (double ai : a)
          z.push_back(1 / ai - 1);
        irred::cosmology::CurvedFLRWPolicy fp;
        fp.relative_tolerance = 1e-11;
        fp.absolute_tolerance_mpc = 1e-9;
        auto gr =
            irred::cosmology::CurvedFLRW({70, .3 + .7 * (1 - as), 0, .7 * as})
                .evaluate(z, fp);
        bool pass = cg.status == S::ok && gr.status == S::ok &&
                    cg.rows.size() == a.size() && gr.rows.size() == a.size();
        long double diff = 0;
        if (pass)
          for (std::size_t i = 0; i < a.size(); ++i) {
            diff = std::max(diff,
                            std::abs(cg.rows[i].expansion_over_anchor_hubble -
                                     gr.rows[i].e));
            pass = pass &&
                   std::abs(cg.rows[i].expansion_over_anchor_hubble -
                            gr.rows[i].e) <= 2e-6 * std::abs(gr.rows[i].e) &&
                   cg.rows[i].distances &&
                   std::abs(cg.rows[i].distances->comoving_mpc -
                            gr.rows[i].radial_mpc) <=
                       1e-4 + 2e-6 * std::abs(gr.rows[i].radial_mpc);
          }
        control("compiled-FLRW-endpoint-" + std::to_string(id++), pass,
                cg.status, diff);
      }
  auto future = irred::cosmology::evolve_chaplygin({70, .3, 0, .7, 1},
                                                   std::array<double, 1>{2});
  control("GCG-future-outside-domain-withheld",
          future.status == S::outside_domain && future.rows.empty(),
          future.status);
  auto pop = irred::gravity::prepare_plummer_population(
      {1e40, 1e19, 6.67430e-11}, std::array<double, 1>{0});
  auto negative = pop.evaluate(
      std::array<irred::gravity::PlummerVelocityRequest, 1>{{{0, -1}}});
  control("negative-speed-refused",
          negative.rows.size() == 1 && negative.rows[0].status != S::ok,
          negative.rows.empty() ? negative.status : negative.rows[0].status);
  control("native-outside-support-diagnostic-zero",
          outside_pass && outside_count == 2 * 4 * radius.size());
  std::cout << "],\"boundary_diagnostics\":{\"rows\":" << boundary_count
            << ",\"ambiguous_rows\":" << ambiguous_count
            << ",\"support_error_interpretation\":\"empirical diagnostic, not "
               "certified "
               "enclosure\"},\"gates\":{\"inference\":\"not_performed\","
               "\"certified_error_bound\":null}}\n";
}
