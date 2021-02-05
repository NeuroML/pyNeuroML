from math import exp
from pyneuroml.pynml import get_value_in_si, print_comment_v


def evaluate_HHExpLinearRate(rate, midpoint, scale, v):
    '''
    Helper for putting values into HHExpLinearRate,
    see also https://www.neuroml.org/NeuroML2CoreTypes/Channels.html#HHExpLinearRate
    '''
    rate_si = get_value_in_si(rate)
    midpoint_si = get_value_in_si(midpoint)
    scale_si = get_value_in_si(scale)
    v_si = get_value_in_si(v)

    print_comment_v('Evaluating: rate * ((v - (midpoint))/scale) / ( 1 - exp(-1 * (v - (midpoint)) / scale)) ')
    print_comment_v('            %s * ((v - (%s))/%s) / ( 1 - exp(-1 * (v - (%s)) / %s))  for v = %s' % (rate, midpoint, scale, midpoint, scale, v))
    print_comment_v('            %s * ((%s - (%s))/%s) / ( 1 - exp(-1 * (%s - (%s)) / %s)) ' % (rate_si, v_si, midpoint_si, scale_si, v_si, midpoint_si, scale_si))
    print_comment_v('            <... type="HHExpLinearRate" rate="%s" midpoint="%s" scale="%s" />' % (rate, midpoint, scale))
    r = rate_si * ((v_si - (midpoint_si)) / scale_si) / (1 - exp(-(v_si - (midpoint_si)) / scale_si))
    print_comment_v('   = %s per_s' % r)
    print_comment_v('   = %s per_ms' % (r / 1000.))


def evaluate_HHSigmoidRate(rate, midpoint, scale, v):
    '''
    Helper for putting values into HHSigmoidRate,
    see also https://www.neuroml.org/NeuroML2CoreTypes/Channels.html#HHSigmoidRate
    '''
    rate_si = get_value_in_si(rate)
    midpoint_si = get_value_in_si(midpoint)
    scale_si = get_value_in_si(scale)
    v_si = get_value_in_si(v)

    print_comment_v('Evaluating: rate / (1 + exp(-1 * (v - midpoint)/scale))  ')
    print_comment_v('            %s / ( 1 + exp(-1 * (v - (%s)) / %s))  for v = %s' % (rate, midpoint, scale, v))
    print_comment_v('            %s / ( 1 + exp(-1 * (%s - (%s)) / %s)) ' % (rate_si, v_si, midpoint_si, scale_si))
    print_comment_v('            <... type="HHSigmoidRate" rate="%s" midpoint="%s" scale="%s" />' % (rate, midpoint, scale))
    r = rate_si / (1 + exp(-1 * (v_si - midpoint_si) / scale_si))
    print_comment_v('   = %s per_s' % r)
    print_comment_v('   = %s per_ms' % (r / 1000.))


def evaluate_HHExpRate(rate, midpoint, scale, v):
    '''
        Helper for putting values into HHExpRate,
        see also https://www.neuroml.org/NeuroML2CoreTypes/Channels.html#HHExpRate
    '''
    rate_si = get_value_in_si(rate)
    midpoint_si = get_value_in_si(midpoint)
    scale_si = get_value_in_si(scale)
    v_si = get_value_in_si(v)

    print_comment_v('Evaluating: rate * exp( (v - midpoint) / scale) ')
    print_comment_v('            %s * exp( (v - (%s)) / %s)  for v = %s' % (rate, midpoint, scale, v))
    print_comment_v('            %s * exp( (%s - (%s)) / %s) ' % (rate_si, v_si, midpoint_si, scale_si))
    print_comment_v('            <... type="HHExpRate" rate="%s" midpoint="%s" scale="%s" />' % (rate, midpoint, scale))
    r = rate_si * exp((v_si - midpoint_si) / scale_si)
    print_comment_v('   = %s per_s' % r)
    print_comment_v('   = %s per_ms' % (r / 1000.))
