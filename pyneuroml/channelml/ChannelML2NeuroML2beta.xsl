<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://www.neuroml.org/schema/neuroml2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:cml="http://morphml.org/channelml/schema" xmlns:meta="http://morphml.org/metadata/schema" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:bqbiol="http://biomodels.net/biology-qualifiers/" xmlns:bqmodel="http://biomodels.net/model-qualifiers/" version="1.0">
  <!--

    This file is used to convert post v1.7.3 ChannelML files to the latest NeuroML 2 format.

    Funding for this work has been received from the Medical Research Council and the 
    Wellcome Trust. This file was initially developed as part of the neuroConstruct project
    
    Author: Padraig Gleeson
    Copyright 2012 University College London
    
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

-->
  <xsl:output method="xml" version="1.0" encoding="iso-8859-1" indent="yes"/>
  <xsl:variable name="neuroLexId">neuroLexId</xsl:variable>
  <xsl:variable name="indent1">
    <xsl:text>
    </xsl:text>
  </xsl:variable>
  <xsl:variable name="indent1_">
    <xsl:text>

    </xsl:text>
  </xsl:variable>
  <xsl:variable name="indent2">
    <xsl:text>
        </xsl:text>
  </xsl:variable>
  <xsl:variable name="indent2_">
    <xsl:text>

        </xsl:text>
  </xsl:variable>
  <xsl:variable name="indent3">
    <xsl:text>
            </xsl:text>
  </xsl:variable>
  <xsl:variable name="indent3_">
    <xsl:text>

            </xsl:text>
  </xsl:variable>
  <xsl:variable name="indent4">
    <xsl:text>
                </xsl:text>
  </xsl:variable>
  <xsl:variable name="indent4_">
    <xsl:text>

                </xsl:text>
  </xsl:variable>
  <xsl:variable name="rateUnits">
    <xsl:choose>
      <xsl:when test="/cml:channelml/@units='Physiological Units'">per_ms</xsl:when>
      <xsl:when test="/cml:channelml/@units='SI Units'">per_s</xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="timeUnits">
    <xsl:choose>
      <xsl:when test="/cml:channelml/@units='Physiological Units'">ms</xsl:when>
      <xsl:when test="/cml:channelml/@units='SI Units'">s</xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="lengthUnits">
    <xsl:choose>
      <xsl:when test="/cml:channelml/@units='Physiological Units'">cm</xsl:when>
      <xsl:when test="/cml:channelml/@units='SI Units'">m</xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="voltageUnits">
    <xsl:choose>
      <xsl:when test="/cml:channelml/@units='Physiological Units'">mV</xsl:when>
      <xsl:when test="/cml:channelml/@units='SI Units'">V</xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="conductanceUnits">
    <xsl:choose>
      <xsl:when test="/cml:channelml/@units='Physiological Units'">mS</xsl:when>
      <xsl:when test="/cml:channelml/@units='SI Units'">S</xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="concentrationUnits">
    <xsl:choose>
      <xsl:when test="/cml:channelml/@units='Physiological Units'">mol_per_cm3</xsl:when>
      <xsl:when test="/cml:channelml/@units='SI Units'">mM</xsl:when>
      <!-- Not really the SI Units, but a much used equivalent-->
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="rhoUnits">
    <xsl:choose>
      <xsl:when test="/cml:channelml/@units='Physiological Units'">mol_per_cm_per_uA_per_ms</xsl:when>
      <!-- TODO... -->
      <xsl:when test="/cml:channelml/@units='SI Units'">mol_per_m_per_A_per_s</xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:template match="/">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="node()|@*">
    <xsl:copy>
      <xsl:apply-templates select="@*"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/cml:channelml">
    <xsl:text>
</xsl:text>
    <xsl:element name="neuroml" namespace="http://www.neuroml.org/schema/neuroml2">
      <xsl:attribute name="schemaLocation" namespace="http://www.w3.org/2001/XMLSchema-instance">http://www.neuroml.org/schema/neuroml2 https://raw.github.com/NeuroML/NeuroML2/development/Schemas/NeuroML2/NeuroML_v2beta4.xsd</xsl:attribute>
      <xsl:attribute name="id">
        <xsl:choose>
          <xsl:when test="count(cml:channel_type) &gt; 0">
            <xsl:value-of select="cml:channel_type/@name"/>
          </xsl:when>
          <xsl:when test="count(cml:synapse_type) &gt; 0">
            <xsl:value-of select="cml:synapse_type/@name"/>
          </xsl:when>
          <xsl:when test="count(cml:ion_concentration) &gt; 0">
            <xsl:value-of select="cml:ion_concentration/@name"/>
          </xsl:when>
        </xsl:choose>
      </xsl:attribute>
      <xsl:call-template name="notes2">
        <xsl:with-param name="indent">
          <xsl:value-of select="$indent1_"/>
        </xsl:with-param>
        <xsl:with-param name="contents" select="meta:notes"/>
      </xsl:call-template>
      <xsl:apply-templates select="cml:channel_type"/>
      <xsl:apply-templates select="cml:synapse_type"/>
      <xsl:apply-templates select="cml:ion_concentration"/>
      <xsl:for-each select="cml:channel_type/cml:current_voltage_relation/cml:conc_factor">
        <xsl:value-of select="$indent1_"/>
        <xsl:element name="ComponentType">
          <xsl:attribute name="name">cond_scaling_<xsl:value-of select="../../@name"/></xsl:attribute>
          <xsl:attribute name="extends">baseConductanceScalingCaDependent</xsl:attribute>
          <xsl:value-of select="$indent2"/>
          <xsl:element name="Constant">
            <xsl:attribute name="name">CONC_SCALE</xsl:attribute>
            <xsl:attribute name="dimension">concentration</xsl:attribute>
            <xsl:attribute name="value">1 <xsl:value-of select="$concentrationUnits"/></xsl:attribute>
          </xsl:element>
          <xsl:value-of select="$indent2_"/>
          <xsl:element name="Dynamics">
            <xsl:value-of select="$indent3"/>
            <xsl:element name="DerivedVariable">
              <xsl:attribute name="name">ca_conc</xsl:attribute>
              <xsl:attribute name="dimension">none</xsl:attribute>
              <xsl:attribute name="value">caConc / CONC_SCALE</xsl:attribute>
            </xsl:element>
            <xsl:variable name="DerivedVariableName">
              <xsl:choose>
                <xsl:when test="contains(@expr, '?')">ConditionalDerivedVariable</xsl:when>
                <xsl:otherwise>DerivedVariable</xsl:otherwise>
              </xsl:choose>
            </xsl:variable>
            <xsl:value-of select="$indent3"/>
            <xsl:element name="{$DerivedVariableName}">
              <xsl:attribute name="name">factor</xsl:attribute>
              <xsl:attribute name="exposure">factor</xsl:attribute>
              <xsl:attribute name="dimension">none</xsl:attribute>
              <xsl:choose>
                <xsl:when test="contains(@expr, '?') = 0">
                  <xsl:attribute name="value">
                    <xsl:value-of select="@expr"/>
                  </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:variable name="cond">
                    <xsl:value-of select="translate(substring-before(@expr,'?'), 'v', 'V')"/>
                  </xsl:variable>
                  <xsl:variable name="valueCondition">
                    <xsl:choose>
                      <xsl:when test="contains($cond, '&gt;=')"><xsl:value-of select="substring-before($cond,'&gt;=')"/> .geq. (<xsl:value-of select="substring-after($cond,'&gt;=')"/>)</xsl:when>
                      <xsl:when test="contains($cond, '&lt;=')"><xsl:value-of select="substring-before($cond,'&lt;=')"/> .leq. (<xsl:value-of select="substring-after($cond,'&lt;=')"/>)</xsl:when>
                      <xsl:when test="contains($cond, '&gt;')"><xsl:value-of select="substring-before($cond,'&gt;')"/> .gt. (<xsl:value-of select="substring-after($cond,'&gt;')"/>)</xsl:when>
                      <xsl:when test="contains($cond, '&lt;')"><xsl:value-of select="substring-before($cond,'&lt;')"/> .lt. (<xsl:value-of select="substring-after($cond,'&lt;')"/>)</xsl:when>
                      <xsl:when test="contains($cond, '==')"><xsl:value-of select="substring-before($cond,'==')"/> .eq. (<xsl:value-of select="substring-after($cond,'==')"/>)</xsl:when>
                      <xsl:otherwise>cc<xsl:value-of select="$cond"/></xsl:otherwise>
                    </xsl:choose>
                  </xsl:variable>
                  <xsl:variable name="valueIfTrue">
                    <xsl:value-of select="translate(substring-before(substring-after(@expr,'?'), ':'), 'v', 'V')"/>
                  </xsl:variable>
                  <xsl:variable name="valueIfFalse">
                    <xsl:value-of select="translate(substring-after(@expr,':'), 'v', 'V')"/>
                  </xsl:variable>
                  <xsl:value-of select="$indent4"/>
                  <xsl:element name="Case">
                    <xsl:attribute name="condition">
                      <xsl:value-of select="$valueCondition"/>
                    </xsl:attribute>
                    <xsl:attribute name="value">
                      <xsl:value-of select="$valueIfTrue"/>
                    </xsl:attribute>
                  </xsl:element>
                  <xsl:value-of select="$indent4"/>
                  <xsl:element name="Case">
                    <xsl:attribute name="value">
                      <xsl:value-of select="$valueIfFalse"/>
                    </xsl:attribute>
                  </xsl:element>
                  <xsl:value-of select="$indent3"/>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:element>
            <xsl:value-of select="$indent2"/>
          </xsl:element>
          <xsl:value-of select="$indent1_"/>
        </xsl:element>
      </xsl:for-each>
      <xsl:for-each select="cml:channel_type/cml:current_voltage_relation/cml:gate/cml:transition |                                               cml:channel_type/cml:current_voltage_relation/cml:gate/cml:time_course |                                               cml:channel_type/cml:current_voltage_relation/cml:gate/cml:steady_state">
        <xsl:variable name="chanType">
          <xsl:choose>
            <xsl:when test="count(../cml:closed_state) &gt; 1">KS</xsl:when>
            <xsl:when test="count(../cml:open_state) &gt; 1">KS</xsl:when>
            <xsl:otherwise>???</xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:if test="@expr_form = 'generic'">
          <xsl:value-of select="$indent1_"/>
          <xsl:element name="ComponentType">
            <xsl:variable name="concentrationDep">
              <xsl:choose>
                <xsl:when test="count(../../cml:conc_dependence) &gt; 0">Conc</xsl:when>
                <xsl:otherwise/>
              </xsl:choose>
            </xsl:variable>
            <xsl:if test="name() = 'transition'">
              <xsl:attribute name="name"><xsl:value-of select="../../../@name"/>_<xsl:value-of select="../@name"/>_<xsl:value-of select="@name"/>_rate</xsl:attribute>
              <xsl:attribute name="extends">baseVoltage<xsl:value-of select="$concentrationDep"/>DepRate</xsl:attribute>
            </xsl:if>
            <xsl:if test="name() = 'time_course'">
              <xsl:attribute name="name"><xsl:value-of select="../../../@name"/>_<xsl:value-of select="../@name"/>_<xsl:value-of select="@name"/>_tau</xsl:attribute>
              <xsl:attribute name="extends">baseVoltage<xsl:value-of select="$concentrationDep"/>DepTime</xsl:attribute>
            </xsl:if>
            <xsl:if test="name() = 'steady_state'">
              <xsl:attribute name="name"><xsl:value-of select="../../../@name"/>_<xsl:value-of select="../@name"/>_<xsl:value-of select="@name"/>_inf</xsl:attribute>
              <xsl:attribute name="extends">baseVoltage<xsl:value-of select="$concentrationDep"/>DepVariable</xsl:attribute>
            </xsl:if>
            <xsl:value-of select="$indent2"/>
            <xsl:element name="Constant">
              <xsl:attribute name="name">TIME_SCALE</xsl:attribute>
              <xsl:attribute name="dimension">time</xsl:attribute>
              <xsl:attribute name="value">1 <xsl:value-of select="$timeUnits"/></xsl:attribute>
            </xsl:element>
            <xsl:value-of select="$indent2"/>
            <xsl:element name="Constant">
              <xsl:attribute name="name">VOLT_SCALE</xsl:attribute>
              <xsl:attribute name="dimension">voltage</xsl:attribute>
              <xsl:attribute name="value">1 <xsl:value-of select="$voltageUnits"/></xsl:attribute>
            </xsl:element>
            <xsl:if test="$concentrationDep = 'Conc'">
              <xsl:value-of select="$indent2"/>
              <xsl:element name="Constant">
                <xsl:attribute name="name">CONC_SCALE</xsl:attribute>
                <xsl:attribute name="dimension">concentration</xsl:attribute>
                <xsl:attribute name="value">1 <xsl:value-of select="$concentrationUnits"/></xsl:attribute>
              </xsl:element>
            </xsl:if>
            <xsl:if test="count(../../cml:offset) &gt; 0">
              <xsl:value-of select="$indent2"/>
              <xsl:element name="Constant">
                <xsl:attribute name="name">offset</xsl:attribute>
                <xsl:attribute name="dimension">voltage</xsl:attribute>
                <xsl:attribute name="value">
                  <xsl:value-of select="../../cml:offset/@value"/>
                  <xsl:value-of select="$voltageUnits"/>
                </xsl:attribute>
              </xsl:element>
            </xsl:if>
            <xsl:if test="count(../../../cml:parameters) &gt; 0">
              <xsl:for-each select="../../../cml:parameters/cml:parameter">
                <xsl:value-of select="$indent2"/>
                <xsl:comment>Note: this parameter (<xsl:value-of select="@name"/>) should ideally be defined only once within the ionChannel! Work in progress...</xsl:comment>
                <xsl:text>
        </xsl:text>
                <xsl:element name="Constant">
                  <xsl:attribute name="name">
                    <xsl:value-of select="@name"/>
                  </xsl:attribute>
                  <xsl:attribute name="dimension">none</xsl:attribute>
                  <xsl:attribute name="value">
                    <xsl:value-of select="@value"/>
                  </xsl:attribute>
                </xsl:element>
              </xsl:for-each>
            </xsl:if>
            <xsl:if test="$chanType = 'KS'">
              <xsl:comment>Since the channel type is <xsl:value-of select="$chanType"/>...</xsl:comment>
              <xsl:text>
        </xsl:text>
              <xsl:element name="Requirement">
                <xsl:attribute name="name">rateScale</xsl:attribute>
                <xsl:attribute name="dimension">none</xsl:attribute>
              </xsl:element>
            </xsl:if>
            <xsl:if test="contains(@expr, 'alpha') or contains(@expr, 'beta')">
              <xsl:value-of select="$indent2"/>
              <xsl:element name="Requirement">
                <xsl:attribute name="name">alpha</xsl:attribute>
                <xsl:attribute name="dimension">per_time</xsl:attribute>
              </xsl:element>
              <xsl:value-of select="$indent2"/>
              <xsl:element name="Requirement">
                <xsl:attribute name="name">beta</xsl:attribute>
                <xsl:attribute name="dimension">per_time</xsl:attribute>
              </xsl:element>
            </xsl:if>
            <xsl:if test="contains(@expr, 'temp_adj_')">
              <xsl:value-of select="$indent2"/>
              <xsl:element name="Requirement">
                <xsl:attribute name="name">rateScale</xsl:attribute>
                <xsl:attribute name="dimension">none</xsl:attribute>
              </xsl:element>
            </xsl:if>
            <xsl:if test="contains(@expr, 'celsius')">
              <xsl:value-of select="$indent2"/>
              <xsl:element name="Constant">
                <xsl:attribute name="name">TEMP_SCALE</xsl:attribute>
                <xsl:attribute name="dimension">temperature</xsl:attribute>
                <xsl:attribute name="value">1 K</xsl:attribute>
              </xsl:element>
              <xsl:value-of select="$indent2"/>
              <xsl:element name="Constant">
                <xsl:attribute name="name">TEMP_OFFSET</xsl:attribute>
                <xsl:attribute name="dimension">temperature</xsl:attribute>
                <xsl:attribute name="value">273.15 K</xsl:attribute>
              </xsl:element>
              <xsl:value-of select="$indent2"/>
              <xsl:element name="Requirement">
                <xsl:attribute name="name">temperature</xsl:attribute>
                <xsl:attribute name="dimension">temperature</xsl:attribute>
              </xsl:element>
            </xsl:if>
            <xsl:value-of select="$indent2_"/>
            <xsl:element name="Dynamics">
              <xsl:choose>
                <xsl:when test="count(../../cml:offset) &gt; 0">
                  <xsl:value-of select="$indent3"/>
                  <xsl:element name="DerivedVariable">
                    <xsl:attribute name="name">V</xsl:attribute>
                    <xsl:attribute name="dimension">none</xsl:attribute>
                    <xsl:attribute name="value">(v - offset) / VOLT_SCALE</xsl:attribute>
                  </xsl:element>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="$indent3"/>
                  <xsl:element name="DerivedVariable">
                    <xsl:attribute name="name">V</xsl:attribute>
                    <xsl:attribute name="dimension">none</xsl:attribute>
                    <xsl:attribute name="value">v / VOLT_SCALE</xsl:attribute>
                  </xsl:element>
                </xsl:otherwise>
              </xsl:choose>
              <xsl:if test="$concentrationDep = 'Conc'">
                <xsl:value-of select="$indent3"/>
                <xsl:element name="DerivedVariable">
                  <xsl:attribute name="name">ca_conc</xsl:attribute>
                  <xsl:attribute name="dimension">none</xsl:attribute>
                  <xsl:attribute name="value">caConc / CONC_SCALE</xsl:attribute>
                </xsl:element>
              </xsl:if>
              <xsl:if test="contains(@expr, 'celsius')">
                <xsl:value-of select="$indent3"/>
                <xsl:element name="DerivedVariable">
                  <xsl:attribute name="name">celsius</xsl:attribute>
                  <xsl:attribute name="dimension">none</xsl:attribute>
                  <xsl:attribute name="value">(temperature - TEMP_OFFSET) / TEMP_SCALE</xsl:attribute>
                </xsl:element>
              </xsl:if>
              <xsl:if test="count(../../../cml:parameters) &gt; 0">
                <xsl:for-each select="../../../cml:parameters/cml:parameter">
                  <xsl:if test="contains(@name, 'v')">
                    <xsl:value-of select="$indent3"/>
                    <xsl:element name="DerivedVariable">
                      <xsl:attribute name="name">
                        <xsl:value-of select="translate(@name, 'v', 'V')"/>
                      </xsl:attribute>
                      <xsl:attribute name="dimension">none</xsl:attribute>
                      <xsl:attribute name="value">
                        <xsl:value-of select="@name"/>
                      </xsl:attribute>
                    </xsl:element>
                  </xsl:if>
                </xsl:for-each>
              </xsl:if>
              <xsl:variable name="value0">
                <xsl:choose>
                  <xsl:when test="contains(@expr, '?')">
                    <xsl:value-of select="translate(substring-before(substring-after(@expr,'?'), ':'), 'v', 'V')"/>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="translate(@expr, 'v', 'V')"/>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:variable>
              <xsl:variable name="temp_adj_factor">temp_adj_<xsl:value-of select="../@name"/></xsl:variable>
              <xsl:variable name="value1">
                <xsl:choose>
                  <xsl:when test="contains($value0, $temp_adj_factor)"><xsl:value-of select="substring-before($value0, $temp_adj_factor)"/>rateScale<xsl:value-of select="substring-after($value0,$temp_adj_factor)"/></xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="$value0"/>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:variable>
              <xsl:variable name="value2">
                <xsl:choose>
                  <xsl:when test="contains($value1, 'alpha')"><xsl:value-of select="substring-before($value1, 'alpha')"/>ALPHA<xsl:value-of select="substring-after($value1,'alpha')"/></xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="$value1"/>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:variable>
              <xsl:variable name="value">
                <xsl:choose>
                  <xsl:when test="contains($value2, 'beta')"><xsl:value-of select="substring-before($value2, 'beta')"/>BETA<xsl:value-of select="substring-after($value2,'beta')"/></xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="$value2"/>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:variable>
              <xsl:if test="contains(@expr, 'alpha') or contains(@expr, 'beta')">
                <xsl:value-of select="$indent3"/>
                <xsl:element name="DerivedVariable">
                  <xsl:attribute name="name">ALPHA</xsl:attribute>
                  <xsl:attribute name="dimension">none</xsl:attribute>
                  <xsl:attribute name="value">alpha * TIME_SCALE</xsl:attribute>
                </xsl:element>
                <xsl:value-of select="$indent3"/>
                <xsl:element name="DerivedVariable">
                  <xsl:attribute name="name">BETA</xsl:attribute>
                  <xsl:attribute name="dimension">none</xsl:attribute>
                  <xsl:attribute name="value">beta * TIME_SCALE</xsl:attribute>
                </xsl:element>
              </xsl:if>
              <xsl:variable name="DerivedVariableName">
                <xsl:choose>
                  <xsl:when test="contains(@expr, '?')">ConditionalDerivedVariable</xsl:when>
                  <xsl:otherwise>DerivedVariable</xsl:otherwise>
                </xsl:choose>
              </xsl:variable>
              <xsl:variable name="valueFinal">
                <xsl:if test="name() = 'transition'">(<xsl:value-of select="$value"/>) / TIME_SCALE</xsl:if>
                <xsl:if test="name() = 'time_course'">(<xsl:value-of select="$value"/>) * TIME_SCALE</xsl:if>
                <xsl:if test="name() = 'steady_state'">
                  <xsl:value-of select="$value"/>
                </xsl:if>
              </xsl:variable>
              <xsl:value-of select="$indent3"/>
              <xsl:element name="{$DerivedVariableName}">
                <xsl:variable name="SCALING">
                  <xsl:choose>
                    <xsl:when test="$chanType = 'KS'">rateScale * </xsl:when>
                    <xsl:otherwise/>
                  </xsl:choose>
                </xsl:variable>
                <xsl:if test="name() = 'transition'">
                  <xsl:attribute name="name">r</xsl:attribute>
                  <xsl:attribute name="exposure">r</xsl:attribute>
                  <xsl:attribute name="dimension">per_time</xsl:attribute>
                </xsl:if>
                <xsl:if test="name() = 'time_course'">
                  <xsl:attribute name="name">t</xsl:attribute>
                  <xsl:attribute name="exposure">t</xsl:attribute>
                  <xsl:attribute name="dimension">time</xsl:attribute>
                </xsl:if>
                <xsl:if test="name() = 'steady_state'">
                  <xsl:attribute name="name">x</xsl:attribute>
                  <xsl:attribute name="exposure">x</xsl:attribute>
                  <xsl:attribute name="dimension">none</xsl:attribute>
                </xsl:if>
                <xsl:choose>
                  <xsl:when test="contains(@expr, '?') = 0">
                    <xsl:attribute name="value">
                      <xsl:value-of select="$SCALING"/>
                      <xsl:value-of select="$valueFinal"/>
                    </xsl:attribute>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:variable name="cond0">
                      <xsl:value-of select="translate(substring-before(@expr,'?'), 'v', 'V')"/>
                    </xsl:variable>
                    <xsl:variable name="cond">
                      <xsl:choose>
                        <xsl:when test="contains($cond0, $temp_adj_factor)"><xsl:value-of select="substring-before($cond0, $temp_adj_factor)"/>rateScale<xsl:value-of select="substring-after($cond0,$temp_adj_factor)"/></xsl:when>
                        <xsl:otherwise>
                          <xsl:value-of select="$cond0"/>
                        </xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="valueCondition1">
                      <xsl:choose>
                        <xsl:when test="contains($cond, '&gt;=')"><xsl:value-of select="substring-before($cond,'&gt;=')"/> .geq. (<xsl:value-of select="substring-after($cond,'&gt;=')"/>)</xsl:when>
                        <xsl:when test="contains($cond, '&lt;=')"><xsl:value-of select="substring-before($cond,'&lt;=')"/> .leq. (<xsl:value-of select="substring-after($cond,'&lt;=')"/>)</xsl:when>
                        <xsl:when test="contains($cond, '&gt;')"><xsl:value-of select="substring-before($cond,'&gt;')"/> .gt. (<xsl:value-of select="substring-after($cond,'&gt;')"/>)</xsl:when>
                        <xsl:when test="contains($cond, '&lt;')"><xsl:value-of select="substring-before($cond,'&lt;')"/> .lt. (<xsl:value-of select="substring-after($cond,'&lt;')"/>)</xsl:when>
                        <xsl:when test="contains($cond, '==')"><xsl:value-of select="substring-before($cond,'==')"/> .eq. (<xsl:value-of select="substring-after($cond,'==')"/>)</xsl:when>
                        <xsl:otherwise>cc<xsl:value-of select="$cond"/></xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="valueCondition2">
                      <xsl:choose>
                        <xsl:when test="contains($valueCondition1, 'alpha')"><xsl:value-of select="substring-before($valueCondition1, 'alpha')"/>ALPHA<xsl:value-of select="substring-after($valueCondition1,'alpha')"/></xsl:when>
                        <xsl:otherwise>
                          <xsl:value-of select="$valueCondition1"/>
                        </xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="valueCondition">
                      <xsl:choose>
                        <xsl:when test="contains($valueCondition2, 'beta')"><xsl:value-of select="substring-before($valueCondition2, 'beta')"/>BETA<xsl:value-of select="substring-after($valueCondition2,'beta')"/></xsl:when>
                        <xsl:otherwise>
                          <xsl:value-of select="$valueCondition2"/>
                        </xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="valueIfFalse1">
                      <xsl:if test="name() = 'transition'">(<xsl:value-of select="translate(substring-after(@expr,':'), 'v', 'V')"/>) / TIME_SCALE</xsl:if>
                      <xsl:if test="name() = 'time_course'">(<xsl:value-of select="translate(substring-after(@expr,':'), 'v', 'V')"/>) * TIME_SCALE</xsl:if>
                      <xsl:if test="name() = 'steady_state'">
                        <xsl:value-of select="translate(substring-after(@expr,':'), 'v', 'V')"/>
                      </xsl:if>
                    </xsl:variable>
                    <xsl:variable name="valueIfFalse2">
                      <xsl:choose>
                        <xsl:when test="contains($valueIfFalse1, 'alpha')"><xsl:value-of select="substring-before($valueIfFalse1, 'alpha')"/>ALPHA<xsl:value-of select="substring-after($valueIfFalse1,'alpha')"/></xsl:when>
                        <xsl:otherwise>
                          <xsl:value-of select="$valueIfFalse1"/>
                        </xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="valueIfFalse">
                      <xsl:choose>
                        <xsl:when test="contains($valueIfFalse2, 'beta')"><xsl:value-of select="substring-before($valueIfFalse2, 'beta')"/>BETA<xsl:value-of select="substring-after($valueIfFalse2,'beta')"/></xsl:when>
                        <xsl:otherwise>
                          <xsl:value-of select="$valueIfFalse2"/>
                        </xsl:otherwise>
                      </xsl:choose>
                    </xsl:variable>
                    <xsl:if test="(contains($valueCondition, 'ALPHA') and contains($valueCondition, 'BETA')) or (contains($valueFinal, 'ALPHA') and contains($valueFinal, 'BETA')) or (contains($valueIfFalse, 'ALPHA') and contains($valueIfFalse, 'BETA'))">
                      <xsl:value-of select="$indent4"/>
                      <xsl:element name="Case">
                        <xsl:attribute name="condition">(ALPHA + BETA) .eq. 0</xsl:attribute>
                        <xsl:attribute name="value">( 0 ) * TIME_SCALE</xsl:attribute>
                      </xsl:element>
                    </xsl:if>
                    <xsl:value-of select="$indent4"/>
                    <xsl:element name="Case">
                      <xsl:attribute name="condition">
                        <xsl:value-of select="$valueCondition"/>
                      </xsl:attribute>
                      <xsl:attribute name="value">
                        <xsl:value-of select="$SCALING"/>
                        <xsl:value-of select="$valueFinal"/>
                      </xsl:attribute>
                    </xsl:element>
                    <xsl:value-of select="$indent4"/>
                    <xsl:element name="Case">
                      <xsl:attribute name="value">
                        <xsl:value-of select="$SCALING"/>
                        <xsl:value-of select="$valueIfFalse"/>
                      </xsl:attribute>
                    </xsl:element>
                    <xsl:value-of select="$indent3"/>
                  </xsl:otherwise>
                </xsl:choose>
                <xsl:if test="name() = 'steady_state' and contains(@expr, 'alpha') and contains(@expr, 'beta')">
                  <!-- ConditionalDerivedVariable_TODO -->
                  <xsl:attribute name="valueCondition">(alpha + beta) .neq. 0</xsl:attribute>
                  <xsl:attribute name="valueIfFalse">0</xsl:attribute>
                </xsl:if>
              </xsl:element>
              <xsl:value-of select="$indent2"/>
            </xsl:element>
            <xsl:value-of select="$indent1_"/>
          </xsl:element>
        </xsl:if>
      </xsl:for-each>
      <xsl:text>

</xsl:text>
    </xsl:element>
  </xsl:template>
  <xsl:template match="cml:ion_concentration">
    <xsl:variable name="ConcModelName">
      <xsl:choose>
        <xsl:when test="count(cml:decaying_pool_model/cml:pool_volume_info) &gt; 0">decayingPoolConcentrationModel</xsl:when>
        <xsl:when test="count(cml:decaying_pool_model/@inv_decay_constant) &gt; 0">fixedFactorConcentrationModelTraub</xsl:when>
        <xsl:otherwise>fixedFactorConcentrationModel</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:text>

    </xsl:text>
    <xsl:element name="{$ConcModelName}">
      <xsl:attribute name="id">
        <xsl:value-of select="@name"/>
      </xsl:attribute>
      <xsl:if test="count(meta:properties/meta:property[@tag=$neuroLexId]) &gt; 0">
        <xsl:attribute name="neuroLexId">
          <xsl:value-of select="meta:properties/meta:property[@tag=$neuroLexId]/@value"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="restingConc">
        <xsl:value-of select="cml:decaying_pool_model/@resting_conc"/>
        <xsl:value-of select="$concentrationUnits"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="count(cml:decaying_pool_model/@decay_constant) &gt; 0">
          <xsl:attribute name="decayConstant">
            <xsl:value-of select="cml:decaying_pool_model/@decay_constant"/>
            <xsl:value-of select="$timeUnits"/>
          </xsl:attribute>
        </xsl:when>
        <xsl:when test="count(cml:decaying_pool_model/@inv_decay_constant) &gt; 0">
          <xsl:attribute name="beta">
            <xsl:value-of select="cml:decaying_pool_model/@inv_decay_constant"/>
            <xsl:value-of select="$rateUnits"/>
          </xsl:attribute>
        </xsl:when>
      </xsl:choose>
      <xsl:attribute name="ion">
        <xsl:value-of select="cml:ion_species/@name"/>
      </xsl:attribute>
      <xsl:if test="count(cml:decaying_pool_model/cml:pool_volume_info) &gt; 0">
        <xsl:attribute name="shellThickness">
          <xsl:value-of select="cml:decaying_pool_model/cml:pool_volume_info/@shell_thickness"/>
          <xsl:value-of select="$lengthUnits"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="count(cml:decaying_pool_model/cml:fixed_pool_info) &gt; 0">
        <xsl:variable name="rhoName">
          <xsl:choose>
            <!-- Only used in https://github.com/OpenSourceBrain/Thalamocortical -->
            <xsl:when test="count(cml:decaying_pool_model/@inv_decay_constant) &gt; 0">phi</xsl:when>
            <xsl:otherwise>rho</xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:choose>
          <!-- Only used in https://github.com/OpenSourceBrain/Thalamocortical -->
          <xsl:when test="count(cml:decaying_pool_model/@inv_decay_constant) &gt; 0">
            <!--TODO: remove need for this factor-->
            <xsl:variable name="phiFactor">
              <xsl:choose>
                <xsl:when test="/cml:channelml/@units='Physiological Units'">1</xsl:when>
                <xsl:when test="/cml:channelml/@units='SI Units'">???</xsl:when>
              </xsl:choose>
            </xsl:variable>
            <xsl:attribute name="phi">
              <xsl:value-of select="$phiFactor * number(cml:decaying_pool_model/cml:fixed_pool_info/cml:phi)"/>
              <xsl:value-of select="$rhoUnits"/>
            </xsl:attribute>
          </xsl:when>
          <xsl:otherwise>
            <!--TODO: remove need for this factor-->
            <xsl:variable name="rhoFactor">
              <xsl:choose>
                <xsl:when test="/cml:channelml/@units='Physiological Units'">1e-9</xsl:when>
                <xsl:when test="/cml:channelml/@units='SI Units'">100</xsl:when>
              </xsl:choose>
            </xsl:variable>
            <xsl:attribute name="rho">
              <xsl:value-of select="$rhoFactor * number(cml:decaying_pool_model/cml:fixed_pool_info/cml:phi)"/>
              <xsl:value-of select="$rhoUnits"/>
            </xsl:attribute>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:if>
    </xsl:element>
  </xsl:template>
  <xsl:template match="cml:synapse_type">
    <xsl:choose>
      <xsl:when test="count(cml:doub_exp_syn) &gt; 0 and count(cml:doub_exp_syn/@rise_time) &gt; 0 and number(cml:doub_exp_syn/@rise_time) &gt; 0 and number(cml:doub_exp_syn/@rise_time) = number(cml:doub_exp_syn/@decay_time)">
        <xsl:value-of select="$indent1_"/>
        <xsl:element name="alphaSynapse">
          <xsl:attribute name="id">
            <xsl:value-of select="@name"/>
          </xsl:attribute>
          <xsl:if test="count(meta:properties/meta:property[@tag=$neuroLexId]) &gt; 0">
            <xsl:attribute name="neuroLexId">
              <xsl:value-of select="meta:properties/meta:property[@tag=$neuroLexId]/@value"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:attribute name="tau">
            <xsl:value-of select="cml:doub_exp_syn/@rise_time"/>
            <xsl:value-of select="$timeUnits"/>
          </xsl:attribute>
          <xsl:attribute name="gbase">
            <xsl:value-of select="cml:doub_exp_syn/@max_conductance"/>
            <xsl:value-of select="$conductanceUnits"/>
          </xsl:attribute>
          <xsl:attribute name="erev">
            <xsl:value-of select="cml:doub_exp_syn/@reversal_potential"/>
            <xsl:value-of select="$voltageUnits"/>
          </xsl:attribute>
          <xsl:call-template name="notes2">
            <xsl:with-param name="indent">
              <xsl:value-of select="$indent2_"/>
            </xsl:with-param>
            <xsl:with-param name="contents" select="meta:notes"/>
          </xsl:call-template>
        </xsl:element>
      </xsl:when>
      <xsl:when test="count(cml:doub_exp_syn) &gt; 0 and count(cml:doub_exp_syn/@rise_time) &gt; 0 and number(cml:doub_exp_syn/@rise_time) &gt; 0">
        <xsl:value-of select="$indent1_"/>
        <xsl:element name="expTwoSynapse">
          <xsl:attribute name="id">
            <xsl:value-of select="@name"/>
          </xsl:attribute>
          <xsl:if test="count(meta:properties/meta:property[@tag=$neuroLexId]) &gt; 0">
            <xsl:attribute name="neuroLexId">
              <xsl:value-of select="meta:properties/meta:property[@tag=$neuroLexId]/@value"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:attribute name="tauRise">
            <xsl:value-of select="cml:doub_exp_syn/@rise_time"/>
            <xsl:value-of select="$timeUnits"/>
          </xsl:attribute>
          <xsl:attribute name="tauDecay">
            <xsl:value-of select="cml:doub_exp_syn/@decay_time"/>
            <xsl:value-of select="$timeUnits"/>
          </xsl:attribute>
          <xsl:attribute name="gbase">
            <xsl:value-of select="cml:doub_exp_syn/@max_conductance"/>
            <xsl:value-of select="$conductanceUnits"/>
          </xsl:attribute>
          <xsl:attribute name="erev">
            <xsl:value-of select="cml:doub_exp_syn/@reversal_potential"/>
            <xsl:value-of select="$voltageUnits"/>
          </xsl:attribute>
          <xsl:call-template name="notes2">
            <xsl:with-param name="indent">
              <xsl:value-of select="$indent2_"/>
            </xsl:with-param>
            <xsl:with-param name="contents" select="meta:notes"/>
          </xsl:call-template>
        </xsl:element>
      </xsl:when>
      <xsl:when test="count(cml:doub_exp_syn) &gt; 0 and (count(cml:doub_exp_syn/@rise_time) = 0 or number(cml:doub_exp_syn/@rise_time) = 0)">
        <xsl:value-of select="$indent1_"/>
        <xsl:element name="expOneSynapse">
          <xsl:attribute name="id">
            <xsl:value-of select="@name"/>
          </xsl:attribute>
          <xsl:if test="count(meta:properties/meta:property[@tag=$neuroLexId]) &gt; 0">
            <xsl:attribute name="neuroLexId">
              <xsl:value-of select="meta:properties/meta:property[@tag=$neuroLexId]/@value"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:attribute name="tauDecay">
            <xsl:value-of select="cml:doub_exp_syn/@decay_time"/>
            <xsl:value-of select="$timeUnits"/>
          </xsl:attribute>
          <xsl:attribute name="gbase">
            <xsl:value-of select="cml:doub_exp_syn/@max_conductance"/>
            <xsl:value-of select="$conductanceUnits"/>
          </xsl:attribute>
          <xsl:attribute name="erev">
            <xsl:value-of select="cml:doub_exp_syn/@reversal_potential"/>
            <xsl:value-of select="$voltageUnits"/>
          </xsl:attribute>
          <xsl:call-template name="notes2">
            <xsl:with-param name="indent">
              <xsl:value-of select="$indent2_"/>
            </xsl:with-param>
            <xsl:with-param name="contents" select="meta:notes"/>
          </xsl:call-template>
        </xsl:element>
      </xsl:when>
      <xsl:when test="count(cml:blocking_syn) &gt; 0">
        <xsl:value-of select="$indent1_"/>
        <xsl:element name="blockingPlasticSynapse">
          <xsl:attribute name="id">
            <xsl:value-of select="@name"/>
          </xsl:attribute>
          <xsl:if test="count(meta:properties/meta:property[@tag=$neuroLexId]) &gt; 0">
            <xsl:attribute name="neuroLexId">
              <xsl:value-of select="meta:properties/meta:property[@tag=$neuroLexId]/@value"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:attribute name="gbase">
            <xsl:value-of select="cml:blocking_syn/@max_conductance"/>
            <xsl:value-of select="$conductanceUnits"/>
          </xsl:attribute>
          <xsl:attribute name="tauRise">
            <xsl:value-of select="cml:blocking_syn/@rise_time"/>
            <xsl:value-of select="$timeUnits"/>
          </xsl:attribute>
          <xsl:attribute name="tauDecay">
            <xsl:value-of select="cml:blocking_syn/@decay_time"/>
            <xsl:value-of select="$timeUnits"/>
          </xsl:attribute>
          <xsl:attribute name="erev">
            <xsl:value-of select="cml:blocking_syn/@reversal_potential"/>
            <xsl:value-of select="$voltageUnits"/>
          </xsl:attribute>
          <xsl:call-template name="notes2">
            <xsl:with-param name="indent">
              <xsl:value-of select="$indent2_"/>
            </xsl:with-param>
            <xsl:with-param name="contents" select="meta:notes"/>
          </xsl:call-template>
          <xsl:call-template name="annotations"/>
          <xsl:apply-templates select="cml:blocking_syn/cml:block"/>
          <xsl:text>

    </xsl:text>
        </xsl:element>
      </xsl:when>
      <xsl:when test="count(cml:electrical_syn) &gt; 0">
        <xsl:value-of select="$indent1_"/>
        <xsl:element name="gapJunction">
          <xsl:attribute name="id">
            <xsl:value-of select="@name"/>
          </xsl:attribute>
          <xsl:attribute name="conductance">
            <xsl:value-of select="cml:electrical_syn/@conductance"/>
            <xsl:value-of select="$conductanceUnits"/>
          </xsl:attribute>
        </xsl:element>
      </xsl:when>
      <xsl:otherwise>
                        Error: that synapse type is not currently supported in ChannelML2NeuroML2.xsl...
                    </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="cml:block">
    <xsl:value-of select="$indent2_"/>
    <xsl:element name="blockMechanism">
      <xsl:attribute name="type">voltageConcDepBlockMechanism</xsl:attribute>
      <xsl:attribute name="species">
        <xsl:value-of select="@species"/>
      </xsl:attribute>
      <xsl:attribute name="blockConcentration">
        <xsl:value-of select="@conc"/>
        <xsl:value-of select="$concentrationUnits"/>
      </xsl:attribute>
      <xsl:attribute name="scalingConc">
        <xsl:value-of select="1 div number(@eta)"/>
        <xsl:value-of select="$concentrationUnits"/>
      </xsl:attribute>
      <xsl:attribute name="scalingVolt">
        <xsl:value-of select="1 div number(@gamma)"/>
        <xsl:value-of select="$voltageUnits"/>
      </xsl:attribute>
    </xsl:element>
  </xsl:template>
  <xsl:template match="cml:channel_type">
    <xsl:variable name="chanType">
      <xsl:for-each select="cml:current_voltage_relation/cml:gate">
        <xsl:if test="count(cml:closed_state) &gt; 1">KS</xsl:if>
        <xsl:if test="count(cml:open_state) &gt; 1">KS</xsl:if>
      </xsl:for-each>
    </xsl:variable>
    <xsl:variable name="ionChanElement">
      <xsl:choose>
        <xsl:when test="contains($chanType, 'KS')">ionChannelKS</xsl:when>
        <xsl:otherwise>ionChannel</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:value-of select="$indent1_"/>
    <xsl:element name="{$ionChanElement}">
      <xsl:attribute name="id">
        <xsl:value-of select="@name"/>
      </xsl:attribute>
      <xsl:if test="count(meta:properties/meta:property[@tag=$neuroLexId]) &gt; 0">
        <xsl:attribute name="neuroLexId">
          <xsl:value-of select="meta:properties/meta:property[@tag=$neuroLexId]/@value"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="count(cml:integrate_and_fire) = 0">
        <xsl:attribute name="conductance">10pS</xsl:attribute>
        <xsl:choose>
          <xsl:when test="contains($chanType, 'KS')">
            <!--<xsl:attribute name="type">ionChannelKS</xsl:attribute>-->
            <xsl:attribute name="species">
              <xsl:value-of select="cml:current_voltage_relation/@ion"/>
            </xsl:attribute>
          </xsl:when>
          <xsl:when test="count(cml:current_voltage_relation/cml:gate) = 0">
            <xsl:attribute name="type">ionChannelPassive</xsl:attribute>
          </xsl:when>
          <xsl:otherwise>
            <xsl:attribute name="type">ionChannelHH</xsl:attribute>
            <xsl:attribute name="species">
              <xsl:value-of select="cml:current_voltage_relation/@ion"/>
            </xsl:attribute>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:if>
      <xsl:call-template name="notes2">
        <xsl:with-param name="indent">
          <xsl:value-of select="$indent2_"/>
        </xsl:with-param>
        <xsl:with-param name="contents" select="meta:notes"/>
      </xsl:call-template>
      <!-- Need to add this after all attributes are added -->
      <xsl:call-template name="annotations"/>
      <xsl:apply-templates select="cml:current_voltage_relation"/>
      <xsl:text>
                            
    </xsl:text>
    </xsl:element>
  </xsl:template>
  <xsl:template match="cml:current_voltage_relation">
    <xsl:choose>
      <xsl:when test="count(cml:integrate_and_fire) &gt; 0"><xsl:apply-templates select="../meta:notes"/><!-- Need to add this after all attributes are added -->
            Integrate and fire not yet implemented....
                    </xsl:when>
      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="@cond_law = 'ohmic'">
            <!-- Need to add this after all attributes are added
                                <xsl:if test="count(../cml:parameters) &gt; 0"> 
                                    <xsl:for-each select="../cml:parameters/cml:parameter">
                                        <xsl:element name="parameter">
                                            <xsl:attribute name="id"><xsl:value-of select="@name"/></xsl:attribute>
                                            <xsl:attribute name="value"><xsl:value-of select="@value"/></xsl:attribute>
                                        </xsl:element>
                                    </xsl:for-each>
                                </xsl:if> -->
            <!--<xsl:comment>Ohmic channel with <xsl:value-of select="count(cml:gate)"/> gates. Note a default single channel conductance of 10 pS has been added...</xsl:comment>-->
            <xsl:apply-templates select="cml:conc_factor"/>
            <xsl:apply-templates select="cml:gate"/>
          </xsl:when>
          <xsl:otherwise>
                                    Not yet implemented....
                            </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="cml:conc_factor">
    <xsl:text>

        </xsl:text>
    <xsl:element name="baseConductanceScalingCaDependent">
      <xsl:attribute name="type">cond_scaling_<xsl:value-of select="../../@name"/></xsl:attribute>
    </xsl:element>
  </xsl:template>
  <xsl:template match="cml:gate">
    <xsl:variable name="gateElement">
      <xsl:choose>
        <xsl:when test="count(cml:closed_state) &gt; 1 or count(cml:open_state) &gt; 1">gateKS</xsl:when>
        <xsl:otherwise>gate</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="gateType">
      <xsl:choose>
        <xsl:when test="count(cml:closed_state) &gt; 1 or count(cml:open_state) &gt; 1">gateKS</xsl:when>
        <xsl:when test="count(cml:transition) = 2 and count(cml:time_course) = 1 and count(cml:steady_state) = 0">gateHHratesTau</xsl:when>
        <xsl:when test="count(cml:transition) = 0 and count(cml:time_course) = 1 and count(cml:steady_state) = 1">gateHHtauInf</xsl:when>
        <xsl:when test="count(cml:transition) = 2 and count(cml:time_course) = 0 and count(cml:steady_state) = 0">gateHHrates</xsl:when>
        <xsl:when test="count(cml:transition) = 2 and count(cml:time_course) = 0 and count(cml:steady_state) = 1">gateHHratesInf</xsl:when>
        <xsl:when test="count(cml:transition) = 2 and count(cml:time_course) = 1 and count(cml:steady_state) = 1">gateHHratesTauInf</xsl:when>
        <xsl:otherwise>Cannot determine form of gate (gateHHrates? gateHHratesInf? etc.)</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:text>

        </xsl:text>
    <xsl:element name="{$gateElement}">
      <xsl:attribute name="id">
        <xsl:value-of select="@name"/>
      </xsl:attribute>
      <xsl:if test="$gateElement = 'gate'">
        <xsl:attribute name="type">
          <xsl:value-of select="$gateType"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="instances">
        <xsl:value-of select="@instances"/>
      </xsl:attribute>
      <xsl:variable name="gateid">
        <xsl:value-of select="@name"/>
      </xsl:variable>
      <xsl:choose>
        <xsl:when test="$gateType = 'gateHHratesTau' or $gateType = 'gateHHtauInf' or $gateType = 'gateHHrates' or $gateType = 'gateHHratesInf' or $gateType = 'gateHHratesTauInf' ">
          <xsl:if test="count(../cml:q10_settings) &gt; 0">
            <!--TODO impl possibility that there are multiple q10s for each gate -->
            <xsl:value-of select="$indent3"/>
            <xsl:element name="q10Settings">
              <xsl:choose>
                <xsl:when test="../cml:q10_settings/@gate">
                  <xsl:choose>
                    <xsl:when test="count(../cml:q10_settings[@gate=$gateid]/@fixed_q10) &gt; 0">
                      <xsl:attribute name="type">q10Fixed</xsl:attribute>
                      <xsl:attribute name="fixedQ10">
                        <xsl:value-of select="../cml:q10_settings[@gate=$gateid]/@fixed_q10"/>
                      </xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:attribute name="type">q10ExpTemp</xsl:attribute>
                      <xsl:attribute name="q10Factor">
                        <xsl:value-of select="../cml:q10_settings[@gate=$gateid]/@q10_factor"/>
                      </xsl:attribute>
                      <xsl:attribute name="experimentalTemp"><xsl:value-of select="../cml:q10_settings[@gate=$gateid]/@experimental_temp"/> degC</xsl:attribute>
                      <!--<xsl:attribute name="celsius">
                                                    <xsl:value-of select="$defaultTemp"/>
                                                    </xsl:attribute>-->
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:choose>
                    <xsl:when test="count(../cml:q10_settings/@fixed_q10) &gt; 0">
                      <xsl:attribute name="type">q10Fixed</xsl:attribute>
                      <xsl:attribute name="fixedQ10">
                        <xsl:value-of select="../cml:q10_settings/@fixed_q10"/>
                      </xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:attribute name="type">q10ExpTemp</xsl:attribute>
                      <xsl:attribute name="q10Factor">
                        <xsl:value-of select="../cml:q10_settings/@q10_factor"/>
                      </xsl:attribute>
                      <xsl:attribute name="experimentalTemp"><xsl:value-of select="../cml:q10_settings/@experimental_temp"/> degC</xsl:attribute>
                      <!--<xsl:attribute name="celsius">
                                                    <xsl:value-of select="$defaultTemp"/>
                                                    </xsl:attribute>-->
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:element>
          </xsl:if>
          <xsl:if test="count(../cml:offset) &gt; 0">
            <xsl:value-of select="$indent3"/>
            <xsl:comment>Note: offset from ChannelML file incorporated into the midpoint of rates!!</xsl:comment>
          </xsl:if>
          <xsl:variable name="o">
            <xsl:value-of select="cml:open_state/@id"/>
          </xsl:variable>
          <xsl:variable name="c">
            <xsl:value-of select="cml:closed_state/@id"/>
          </xsl:variable>
          <xsl:for-each select="cml:transition">
            <xsl:if test="@from = $c and @to = $o">
              <xsl:text>
            </xsl:text>
              <xsl:element name="forwardRate">
                <xsl:apply-templates select="."/>
              </xsl:element>
            </xsl:if>
            <xsl:if test="@from = $o and @to = $c">
              <xsl:text>
            </xsl:text>
              <xsl:element name="reverseRate">
                <xsl:apply-templates select="."/>
              </xsl:element>
            </xsl:if>
          </xsl:for-each>
          <xsl:for-each select="cml:time_course">
            <xsl:if test="@from = $c and @to = $o">
              <xsl:text>
            </xsl:text>
              <xsl:element name="timeCourse">
                <xsl:apply-templates select="."/>
              </xsl:element>
            </xsl:if>
          </xsl:for-each>
          <xsl:for-each select="cml:steady_state">
            <xsl:if test="@from = $c and @to = $o">
              <xsl:text>
            </xsl:text>
              <xsl:element name="steadyState">
                <xsl:apply-templates select="."/>
              </xsl:element>
            </xsl:if>
          </xsl:for-each>
        </xsl:when>
        <xsl:when test="$gateType = 'gateKS' ">
          <xsl:if test="count(../cml:q10_settings) &gt; 0">
            <!--TODO impl possibility that there are multiple q10s for each gate -->
            <xsl:value-of select="$indent3"/>
            <xsl:element name="q10Settings">
              <xsl:choose>
                <xsl:when test="../cml:q10_settings/@gate">
                  <xsl:choose>
                    <xsl:when test="count(../cml:q10_settings[@gate=$gateid]/@fixed_q10) &gt; 0">
                      <xsl:attribute name="type">q10Fixed</xsl:attribute>
                      <xsl:attribute name="fixedQ10">
                        <xsl:value-of select="../cml:q10_settings[@gate=$gateid]/@fixed_q10"/>
                      </xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:attribute name="type">q10ExpTemp</xsl:attribute>
                      <xsl:attribute name="q10Factor">
                        <xsl:value-of select="../cml:q10_settings[@gate=$gateid]/@q10_factor"/>
                      </xsl:attribute>
                      <xsl:attribute name="experimentalTemp"><xsl:value-of select="../cml:q10_settings[@gate=$gateid]/@experimental_temp"/> degC</xsl:attribute>
                      <!--<xsl:attribute name="celsius">
                                                    <xsl:value-of select="$defaultTemp"/>
                                                    </xsl:attribute>-->
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:choose>
                    <xsl:when test="count(../cml:q10_settings/@fixed_q10) &gt; 0">
                      <xsl:attribute name="type">q10Fixed</xsl:attribute>
                      <xsl:attribute name="fixedQ10">
                        <xsl:value-of select="../cml:q10_settings/@fixed_q10"/>
                      </xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:attribute name="type">q10ExpTemp</xsl:attribute>
                      <xsl:attribute name="q10Factor">
                        <xsl:value-of select="../cml:q10_settings/@q10_factor"/>
                      </xsl:attribute>
                      <xsl:attribute name="experimentalTemp"><xsl:value-of select="../cml:q10_settings/@experimental_temp"/> degC</xsl:attribute>
                      <!--<xsl:attribute name="celsius">
                                                    <xsl:value-of select="$defaultTemp"/>
                                                    </xsl:attribute>-->
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:element>
          </xsl:if>
          <xsl:for-each select="cml:closed_state">
            <xsl:text>
            </xsl:text>
            <xsl:element name="closedState">
              <xsl:attribute name="id">
                <xsl:value-of select="@id"/>
              </xsl:attribute>
            </xsl:element>
          </xsl:for-each>
          <xsl:for-each select="cml:open_state">
            <xsl:text>
            </xsl:text>
            <xsl:element name="openState">
              <xsl:attribute name="id">
                <xsl:value-of select="@id"/>
              </xsl:attribute>
            </xsl:element>
          </xsl:for-each>
          <xsl:for-each select="cml:transition">
            <xsl:comment>Transition: <xsl:value-of select="@name"/>, <xsl:value-of select="@from"/> -&gt; <xsl:value-of select="@to"/> </xsl:comment>
            <xsl:choose>
              <xsl:when test="contains(@name,'alpha')">
                <xsl:text>
            </xsl:text>
                <xsl:element name="forwardTransition">
                  <xsl:attribute name="id">
                    <xsl:value-of select="@name"/>
                  </xsl:attribute>
                  <xsl:attribute name="from">
                    <xsl:value-of select="@from"/>
                  </xsl:attribute>
                  <xsl:attribute name="to">
                    <xsl:value-of select="@to"/>
                  </xsl:attribute>
                  <xsl:text>
                </xsl:text>
                  <xsl:element name="rate">
                    <!--<xsl:attribute name="id" ><xsl:value-of select="@name"/>_rate</xsl:attribute>-->
                    <xsl:attribute name="type"><xsl:value-of select="../../../@name"/>_<xsl:value-of select="../@name"/>_<xsl:value-of select="@name"/>_rate</xsl:attribute>
                  </xsl:element>
                  <xsl:text>
            </xsl:text>
                </xsl:element>
              </xsl:when>
              <xsl:when test="contains(@name,'beta')">
                <xsl:text>
            </xsl:text>
                <xsl:element name="reverseTransition">
                  <xsl:attribute name="id">
                    <xsl:value-of select="@name"/>
                  </xsl:attribute>
                  <xsl:attribute name="from">
                    <xsl:value-of select="@to"/>
                  </xsl:attribute>
                  <xsl:attribute name="to">
                    <xsl:value-of select="@from"/>
                  </xsl:attribute>
                  <xsl:text>
                </xsl:text>
                  <xsl:element name="rate">
                    <!--<xsl:attribute name="id" ><xsl:value-of select="@name"/>_rate</xsl:attribute>-->
                    <xsl:attribute name="type"><xsl:value-of select="../../../@name"/>_<xsl:value-of select="../@name"/>_<xsl:value-of select="@name"/>_rate</xsl:attribute>
                  </xsl:element>
                  <xsl:text>
            </xsl:text>
                </xsl:element>
              </xsl:when>
              <xsl:otherwise>
        Error. The current implementation of this mapping from ChannelML to NeuroML2 depends on the 
        names of the transitions containing 'alpha' or 'beta' to determine whether they are forward or reverse transitions respectively.
        A more intelligent way to determine this should be possible, but is not yet implemented
                                        </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
        </xsl:when>
        <xsl:otherwise><xsl:value-of select="$gateType"/>: not yet implemented!!</xsl:otherwise>
      </xsl:choose>
      <xsl:text>
        </xsl:text>
    </xsl:element>
  </xsl:template>
  <xsl:template match="cml:transition">
    <xsl:choose>
      <xsl:when test="@expr_form='exponential'">
        <xsl:attribute name="type">HHExpRate</xsl:attribute>
      </xsl:when>
      <xsl:when test="@expr_form='exp_linear'">
        <xsl:attribute name="type">HHExpLinearRate</xsl:attribute>
      </xsl:when>
      <xsl:when test="@expr_form='sigmoid'">
        <xsl:attribute name="type">HHSigmoidRate</xsl:attribute>
      </xsl:when>
      <xsl:when test="@expr_form='generic'">
        <xsl:attribute name="type"><xsl:value-of select="../../../@name"/>_<xsl:value-of select="../@name"/>_<xsl:value-of select="@name"/>_rate</xsl:attribute>
      </xsl:when>
      <xsl:otherwise>
        <xsl:attribute name="type">Not yet implemented!</xsl:attribute>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:variable name="sigmoidFactor">
      <xsl:choose>
        <xsl:when test="@expr_form='sigmoid'">-1</xsl:when>
        <xsl:otherwise>1</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:if test="count(@rate) &gt; 0">
      <xsl:attribute name="rate">
        <xsl:value-of select="@rate"/>
        <xsl:value-of select="$rateUnits"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="count(@scale) &gt; 0">
      <xsl:attribute name="scale">
        <xsl:value-of select="number(@scale) * $sigmoidFactor"/>
        <xsl:value-of select="$voltageUnits"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:variable name="midpoint">
      <xsl:choose>
        <xsl:when test="count(../../cml:offset) &gt; 0">
          <xsl:value-of select="number(@midpoint) + number(../../cml:offset/@value)"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="@midpoint"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:if test="count(@midpoint) &gt; 0">
      <xsl:attribute name="midpoint">
        <xsl:value-of select="$midpoint"/>
        <xsl:value-of select="$voltageUnits"/>
      </xsl:attribute>
    </xsl:if>
  </xsl:template>
  <xsl:template match="cml:time_course">
    <xsl:choose>
      <!--  Note: time course would not normally be fit to exp/exp linear etc!-->
      <xsl:when test="@expr_form='generic'">
        <xsl:attribute name="type"><xsl:value-of select="../../../@name"/>_<xsl:value-of select="../@name"/>_<xsl:value-of select="@name"/>_tau</xsl:attribute>
      </xsl:when>
      <xsl:otherwise>
        <xsl:attribute name="type">Use of sigmoid/exp/explinear in time_course is not yet implemented! Use a generic expression instead.</xsl:attribute>
      </xsl:otherwise>
    </xsl:choose>
    <!--
            <xsl:variable name="sigmoidFactor"><xsl:choose>
                <xsl:when test="@expr_form='sigmoid'">-1</xsl:when>
                <xsl:otherwise>1</xsl:otherwise>
            </xsl:choose></xsl:variable>

            <xsl:if test="count(@rate) &gt; 0"><xsl:attribute name="rate"><xsl:value-of select="@rate"/></xsl:attribute></xsl:if>
            <xsl:if test="count(@scale) &gt; 0"><xsl:attribute name="scale"><xsl:value-of select="number(@scale) * $sigmoidFactor"/><xsl:value-of select="$voltageUnits"/></xsl:attribute></xsl:if>

            <xsl:variable name="midpoint"><xsl:choose>
                <xsl:when test="count(../../cml:offset) &gt; 0"><xsl:value-of select="number(@midpoint) + number(../../cml:offset/@value)"/></xsl:when>
                <xsl:otherwise><xsl:value-of select="@midpoint"/></xsl:otherwise>
            </xsl:choose></xsl:variable>

            <xsl:if test="count(@midpoint) &gt; 0"><xsl:attribute name="midpoint"><xsl:value-of select="$midpoint"/><xsl:value-of select="$voltageUnits"/></xsl:attribute></xsl:if>-->
  </xsl:template>
  <xsl:template match="cml:steady_state">
    <xsl:choose>
      <xsl:when test="@expr_form='exponential'">
        <xsl:attribute name="type">HHExpVariable</xsl:attribute>
      </xsl:when>
      <xsl:when test="@expr_form='exp_linear'">
        <xsl:attribute name="type">HHExpLinearVariable</xsl:attribute>
      </xsl:when>
      <xsl:when test="@expr_form='sigmoid'">
        <xsl:attribute name="type">HHSigmoidVariable</xsl:attribute>
      </xsl:when>
      <xsl:when test="@expr_form='generic'">
        <xsl:attribute name="type"><xsl:value-of select="../../../@name"/>_<xsl:value-of select="../@name"/>_<xsl:value-of select="@name"/>_inf</xsl:attribute>
      </xsl:when>
      <xsl:otherwise>
        <xsl:attribute name="type">Not yet implemented!</xsl:attribute>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:variable name="sigmoidFactor">
      <xsl:choose>
        <xsl:when test="@expr_form='sigmoid'">-1</xsl:when>
        <xsl:otherwise>1</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:if test="count(@rate) &gt; 0">
      <xsl:attribute name="rate">
        <xsl:value-of select="@rate"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="count(@scale) &gt; 0">
      <xsl:attribute name="scale">
        <xsl:value-of select="number(@scale) * $sigmoidFactor"/>
        <xsl:value-of select="$voltageUnits"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:variable name="midpoint">
      <xsl:choose>
        <xsl:when test="count(../../cml:offset) &gt; 0">
          <xsl:value-of select="number(@midpoint) + number(../../cml:offset/@value)"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="@midpoint"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:if test="count(@midpoint) &gt; 0">
      <xsl:attribute name="midpoint">
        <xsl:value-of select="$midpoint"/>
        <xsl:value-of select="$voltageUnits"/>
      </xsl:attribute>
    </xsl:if>
  </xsl:template>
  <xsl:template name="notes2" match="meta:notes">
    <xsl:param name="contents"/>
    <xsl:param name="indent"/>
    <!-- Catching a single quotation in the notes which could confuse a parser -->
    <xsl:variable name="origNotes">
      <xsl:value-of select="$contents"/>
    </xsl:variable>
    <xsl:variable name="quot">'</xsl:variable>
    <xsl:variable name="accent">`</xsl:variable>
    <xsl:value-of select="$indent"/>
    <xsl:element name="notes">
      <xsl:value-of select="translate($origNotes, $quot, $accent)"/>
    </xsl:element>
  </xsl:template>
  <xsl:template name="annotations">
    <xsl:if test="count(meta:publication) &gt; 0 or count(meta:neuronDBref) &gt; 0">
      <xsl:text>
                
        </xsl:text>
      <xsl:element name="annotation">
        <xsl:text>
            </xsl:text>
        <xsl:element name="rdf:RDF">
          <xsl:text>
                </xsl:text>
          <xsl:element name="rdf:Description">
            <xsl:attribute name="rdf:about">
              <xsl:value-of select="@name"/>
            </xsl:attribute>
            <xsl:text>
                    </xsl:text>
            <xsl:apply-templates select="meta:publication"/>
            <xsl:apply-templates select="meta:neuronDBref"/>
          </xsl:element>
          <xsl:text>
            </xsl:text>
        </xsl:element>
        <xsl:text>
        </xsl:text>
      </xsl:element>
    </xsl:if>
  </xsl:template>
  <xsl:template name="publication" match="meta:publication">
    <xsl:text>
                    </xsl:text>
    <xsl:element name="bqmodel:isDescribedBy">
      <xsl:text>
                        </xsl:text>
      <xsl:element name="rdf:Bag">
        <xsl:text>
                            </xsl:text>
        <xsl:element name="rdf:li">
          <xsl:value-of select="meta:fullTitle"/>
        </xsl:element>
        <xsl:text>
                            </xsl:text>
        <xsl:element name="rdf:li">
          <xsl:attribute name="rdf:resource">
            <xsl:value-of select="meta:pubmedRef"/>
          </xsl:attribute>
        </xsl:element>
        <xsl:text>
                        </xsl:text>
      </xsl:element>
      <xsl:text>
                    </xsl:text>
    </xsl:element>
    <xsl:text>

                </xsl:text>
  </xsl:template>
  <xsl:template name="neuronDBref" match="meta:neuronDBref">
    <xsl:text>
                    </xsl:text>
    <xsl:element name="bqbiol:isVersionOf">
      <xsl:text>
                        </xsl:text>
      <xsl:element name="rdf:Bag">
        <xsl:text>
                            </xsl:text>
        <xsl:element name="rdf:li">
          <xsl:value-of select="meta:modelName"/>
        </xsl:element>
        <xsl:text>
                            </xsl:text>
        <xsl:element name="rdf:li">
          <xsl:attribute name="rdf:resource">
            <xsl:value-of select="meta:uri"/>
          </xsl:attribute>
        </xsl:element>
        <xsl:text>
                        </xsl:text>
      </xsl:element>
      <xsl:text>
                    </xsl:text>
    </xsl:element>
    <xsl:text>

                </xsl:text>
  </xsl:template>
</xsl:stylesheet>
