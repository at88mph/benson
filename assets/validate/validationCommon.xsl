<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                version="1.0">

    <!--
      -  report the result of a test. This template should be overridden
      -    for the appropriate output format (plain text, html, etc.).  This
      -    default implementation returns an XML encoding.  The implementation
      -    should honor the global verbosity parameter (see its documentation). 
      -  @param item    the unique code for the test
      -  @param status  boolean (or string=true or false) indicating whether 
      -                   the test passed.
      -  @param type    the type of test.  This should be the string status code 
      -                   to given if the test did not pass.
      -  @param desc    a human-readable statement of what was tested.
      -  
      -->
    <xsl:template name="reportResult">
       <xsl:param name="item">unspecified</xsl:param>
       <xsl:param name="status" select="true()"/>
       <xsl:param name="type" select="'fail'"/>
       <xsl:param name="label"/>
       <xsl:param name="desc"/>

       <xsl:if test="not(contains($ignore, concat(' ',$item,' '))) and 
                     ((string($status)='false' and 
                       contains($verbosity, concat(' ',$type,' ')) ) or
                      (string($status)='true' and 
                       contains($verbosity, ' pass ') ))">
          <xsl:variable name="stat">
             <xsl:choose>
                <xsl:when test="string($status)='true'">pass</xsl:when>
                <xsl:otherwise><xsl:value-of select="$type"/></xsl:otherwise>
             </xsl:choose>
          </xsl:variable>

          <xsl:text>    </xsl:text>
          <test item="{$item}" status="{$stat}">
             <xsl:if test="$label != ''">
                <xsl:attribute name="label">
                   <xsl:value-of select="$label"/>
                </xsl:attribute>
             </xsl:if>
             <xsl:value-of select="$desc"/>
          </test><xsl:text>
</xsl:text>
       </xsl:if>
    </xsl:template>

</xsl:stylesheet>
