"""Independent coordinate/prior controls; no CLASS, data, sampler or SDK import."""
import importlib.util
import math
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / "experiments/sn-relative-reference/coordinates.py"
spec = importlib.util.spec_from_file_location("sn_relative_coordinates", source)
coordinates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coordinates)


class RelativeCoordinates(unittest.TestCase):
    def test_roundtrips_interior_and_bound_adjacent(self):
        # Distances exceed inverse-roundoff; no boundary coercion is admitted.
        points = [(0.023, 0.13, 70.0, -19.0)]
        for bits in range(16):
            points.append(tuple(lo + (hi-lo)*(1e-10 if not bits & (1 << i) else 1-1e-10)
                                for i, (lo, hi) in enumerate(coordinates.BOUNDS)))
        for physical in points:
            recovered = coordinates.inverse(coordinates.forward(physical))
            self.assertIsNotNone(recovered)
            for expected, actual in zip(physical, recovered):
                self.assertLessEqual(abs(actual-expected), 8*math.ulp(expected))

    def test_analytic_jacobian_independent_finite_difference(self):
        u = (0.023, 0.3122448979591837, math.log(0.7), -18.225490200071284)
        # Four-dimensional determinant via elimination, independent of formula.
        columns = []
        for i in range(4):
            step = 1e-6 if i else 1e-7
            left, right = list(u), list(u)
            left[i] -= step; right[i] += step
            xl, xr = coordinates.inverse(left), coordinates.inverse(right)
            columns.append([(b-a)/(2*step) for a, b in zip(xl, xr)])
        matrix = [[columns[j][i] for j in range(4)] for i in range(4)]
        determinant = 1.0
        for i in range(4):
            pivot = matrix[i][i]; determinant *= pivot
            for row in range(i+1, 4):
                factor = matrix[row][i]/pivot
                for col in range(i+1, 4):
                    matrix[row][col] -= factor*matrix[i][col]
        self.assertAlmostEqual(math.log(abs(determinant)), coordinates.log_jacobian(u), delta=2e-8)

    def test_coupled_support_and_no_clipping(self):
        u = list(coordinates.forward((0.023, 0.13, 70.0, -19.0)))
        for i, value in ((0, .029), (1, 10.0), (2, 1000.0), (3, -100.0)):
            proposal = u.copy(); proposal[i] = value
            self.assertIsNone(coordinates.inverse(proposal))
            self.assertEqual(coordinates.uniform_control_target(proposal), -math.inf)
            self.assertEqual(proposal[i], value)

    def test_physical_density_and_jacobian_once(self):
        self.assertAlmostEqual(math.exp(coordinates.LOG_PRIOR), 6.25, delta=1e-13)
        for H0 in (55.0, 70.0, 85.0):
            u = coordinates.forward((.023, .13, H0, -19.0))
            expected = math.log(6.25 * H0 * (H0/100.0)**2)
            self.assertAlmostEqual(coordinates.uniform_control_target(u), expected, delta=2e-15)

    def test_nonfinite_is_refusal_not_prior_exclusion(self):
        with self.assertRaises(ValueError):
            coordinates.inverse((.023, .3, float("nan"), -19.0))


if __name__ == "__main__":
    unittest.main()
