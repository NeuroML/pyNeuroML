from math import exp
from pyneuroml.pynml import get_value_in_si
import logging


logger = logging.getLogger(__name__)


def evaluate_HHExpLinearRate(rate, midpoint, scale, v):
    """
    Helper for putting values into HHExpLinearRate, see also
    https://docs.neuroml.org/Userdocs/Schemas/Channels.html#hhexplinearrate
    """
    rate_si = get_value_in_si(rate)
    midpoint_si = get_value_in_si(midpoint)
    scale_si = get_value_in_si(scale)
    v_si = get_value_in_si(v)

    logger.info(
        "Evaluating: rate * ((v - (midpoint))/scale) / ( 1 - exp(-1 * (v - (midpoint)) / scale)) "
    )
    logger.info(
        "            %s * ((v - (%s))/%s) / ( 1 - exp(-1 * (v - (%s)) / %s))  for v = %s"
        % (rate, midpoint, scale, midpoint, scale, v)
    )
    logger.info(
        "            %s * ((%s - (%s))/%s) / ( 1 - exp(-1 * (%s - (%s)) / %s)) "
        % (rate_si, v_si, midpoint_si, scale_si, v_si, midpoint_si, scale_si)
    )
    logger.info(
        '            <... type="HHExpLinearRate" rate="%s" midpoint="%s" scale="%s" />'
        % (rate, midpoint, scale)
    )
    r = (
        rate_si
        * ((v_si - (midpoint_si)) / scale_si)
        / (1 - exp(-(v_si - (midpoint_si)) / scale_si))
    )
    logger.info("   = %s per_s" % r)
    logger.info("   = %s per_ms" % (r / 1000.0))


def evaluate_HHSigmoidRate(rate, midpoint, scale, v):
    """
    Helper for putting values into HHSigmoidRate, see also
    https://docs.neuroml.org/Userdocs/Schemas/Channels.html#hhsigmoidrate
    """
    rate_si = get_value_in_si(rate)
    midpoint_si = get_value_in_si(midpoint)
    scale_si = get_value_in_si(scale)
    v_si = get_value_in_si(v)

    logger.info("Evaluating: rate / (1 + exp(-1 * (v - midpoint)/scale))  ")
    logger.info(
        "            %s / ( 1 + exp(-1 * (v - (%s)) / %s))  for v = %s"
        % (rate, midpoint, scale, v)
    )
    logger.info(
        "            %s / ( 1 + exp(-1 * (%s - (%s)) / %s)) "
        % (rate_si, v_si, midpoint_si, scale_si)
    )
    logger.info(
        '            <... type="HHSigmoidRate" rate="%s" midpoint="%s" scale="%s" />'
        % (rate, midpoint, scale)
    )
    r = rate_si / (1 + exp(-1 * (v_si - midpoint_si) / scale_si))
    logger.info("   = %s per_s" % r)
    logger.info("   = %s per_ms" % (r / 1000.0))


def evaluate_HHExpRate(rate, midpoint, scale, v):
    """
    Helper for putting values into HHExpRate, see also
    https://docs.neuroml.org/Userdocs/Schemas/Channels.html#hhexprate
    """
    rate_si = get_value_in_si(rate)
    midpoint_si = get_value_in_si(midpoint)
    scale_si = get_value_in_si(scale)
    v_si = get_value_in_si(v)

    logger.info("Evaluating: rate * exp( (v - midpoint) / scale) ")
    logger.info(
        "            %s * exp( (v - (%s)) / %s)  for v = %s"
        % (rate, midpoint, scale, v)
    )
    logger.info(
        "            %s * exp( (%s - (%s)) / %s) "
        % (rate_si, v_si, midpoint_si, scale_si)
    )
    logger.info(
        '            <... type="HHExpRate" rate="%s" midpoint="%s" scale="%s" />'
        % (rate, midpoint, scale)
    )
    r = rate_si * exp((v_si - midpoint_si) / scale_si)
    logger.info("   = %s per_s" % r)
    logger.info("   = %s per_ms" % (r / 1000.0))
