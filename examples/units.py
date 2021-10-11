from pyneuroml import pynml


def test_conversion(nml2_quantity, unit, expected, should_fail=False):
    try:
        val = pynml.convert_to_units(nml2_quantity, unit)
        print(
            "  Converted %s -> %s %s (expecting: %s)"
            % (nml2_quantity, val, unit, expected)
        )
        assert abs(val / expected - 1) < 1e-12
    except Exception as e:
        assert should_fail
        print("Correctly caught exception: %s" % e)


test_conversion("-60 mV", "V", -0.06)
test_conversion("0.01 V", "mV", 10)
test_conversion("120 S_per_cm2", "mS_per_cm2", 120000)
test_conversion("-40 degC", "K", 233.15)
test_conversion("400 K", "degC", 126.85)
test_conversion("2 hour", "s", 7200)
test_conversion("50 min", "hour", 0.833333333333)
test_conversion("400 K", "mV", 111, True)
