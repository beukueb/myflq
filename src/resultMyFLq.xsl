<?xml version="1.0"?>
<!-- resultMyFLq.xsl -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" indent="yes"/>

  <xsl:param name="appcontext" select="'webapp'"/>
  <xsl:param name="profilethreshold" select="20"/>

  <xsl:template match="/"> 
    <xsl:apply-templates select="results"/>
  </xsl:template>

  <xsl:template match="results">
    <xsl:choose>
      <xsl:when test="$appcontext = 'webapp'">
	<xsl:call-template name="webapp"/>
      </xsl:when>
      <xsl:when test="$appcontext = 'basespace'">
	<xsl:call-template name="basespace"/>
      </xsl:when>
      <xsl:otherwise>
	<xsl:text>Application context not known!</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:call-template name="javascript"/>
  </xsl:template>

  <xsl:template name="webapp">
    <html>
      <head>
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.0/jquery.min.js"></script>
	<link rel="stylesheet" href="https://dl.dropboxusercontent.com/u/30816694/CSS/resultMyFLq_XSLT.css" type="text/css" />
      </head>
      <body>
	<div class="resultMyFLq">
	  <h1> Results for <xsl:value-of select="@sample"/> (threshold: <xsl:value-of select="format-number(number(@thresholdUsed),'0.00%')"/>) </h1>
	  <p style="margin-top: -20px;"><span class="hideInProfile"><br />After reviewing all loci, press here to show only selected alleles. </span><button id="profileButton" onclick="processLoci()">Make profile</button><span class="hideInProfile"><br />If you need to make changes afterwards, refresh this page.<br />The results can be saved in the newly generated page.</span></p>
	  <xsl:apply-templates select="locus"/>
	</div>
      </body> 
    </html>
  </xsl:template>

  <xsl:template name="basespace">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.0/jquery.min.js"></script>
    <div class="resultMyFLq">
      <h1> Results for <xsl:value-of select="@sample"/> (threshold: <xsl:value-of select="format-number(number(@thresholdUsed),'0.00%')"/>) </h1>
      <p>After reviewing all loci, press here to show only selected alleles <button onclick="processLoci()">Make profile</button></p>
      <xsl:apply-templates select="locus"/>
    </div>
  </xsl:template>
  
  <xsl:template match="locus">
    <div class="locus" style="margin-top: 20px;">
      <xsl:variable name="locusName" select="@name"/>
      <div class="locusHeader" style="width: 900px; height: 135px; border:1px solid blue;">
	<div style="display: block; float: left; width: 280px;"><h2>Locus <xsl:value-of select="@name"/></h2></div>
	<div style="display: block; float: left; width: 580px;" class="locusStats">
	  <h3>General stats</h3>
	  <p>
	    All data &#8594; total reads: <xsl:value-of select="@reads"/>, total unique reads: <xsl:value-of select="@uniqueReads"/><br />
	    Filtered data &#8594; Filtered reads: <xsl:value-of select="@readsFiltered"/>, filtered unique reads: <xsl:value-of select="@uniqueFiltered"/><br />
	    Reads with a negative sized region of interest: <xsl:value-of select="@badReads"/><br />
	  </p>
	</div>
      </div>
      <div class="alleleCandidates" style="clear: both; margin-top: -15px">
	<h3>Allele candidates</h3>
	<xsl:for-each select="alleleCandidate">
	  <xsl:choose>
	    <xsl:when test="position() > 10">&#xA;
	      <div class="alleleCandidate hiddenCandidate {$locusName} {position()}">
	      <!--span class="{$locusName}" style="display:none;"-->
	        <xsl:apply-templates select="."/>
	      </div>	
	    </xsl:when>
	    <xsl:otherwise>
	      <div class="alleleCandidate {$locusName} {position()}">
		<xsl:apply-templates select="."/>
	      </div>
	    </xsl:otherwise>
	  </xsl:choose>
	</xsl:for-each>
	<xsl:if test="count(alleleCandidate) > 10">
	  <p class="hideInProfile">More than 10 allele candidates <button type="button" id="allelebutton" class="{concat('show',$locusName)}" onclick="$('div.{$locusName}.hiddenCandidate').toggle()">Show all</button></p>
	</xsl:if>
      </div>
    </div>
  </xsl:template>
  
  <xsl:template match="alleleCandidate">
    <!--xsl:param name="locusName"/-->
    <xsl:variable name="locusName" select="../@name"/>
    <h4>
      Index <xsl:number format="1, "/>abundance = <xsl:value-of select="format-number(number(substring(@abundance,0,string-length(@abundance)-1)) div 100,'00.00%')"/>, DB-name =
      <!--xsl:value-of select="@db-name"/>.-->
      <xsl:call-template name="add-whitespace">
	<xsl:with-param name="i" select="4 - string-length(@db-name)"/>
	<xsl:with-param name="str" select="concat(@db-name,'.')"/>
	<xsl:with-param name="where" select="'after'"/>
      </xsl:call-template>
      <span class="hideInProfile">Select for profile:</span>
      <!--input type="checkbox" name="{$locusName}" value="{position}" checked="True"/-->
      <xsl:choose>
	<xsl:when test="number(substring(@abundance,0,string-length(@abundance)-1)) >= $profilethreshold">
	  <input type="checkbox" name="{$locusName}" value="{position}" checked="True" class="hideInProfile"/>
	</xsl:when>
	<xsl:otherwise>
	  <input type="checkbox" name="{$locusName}" value="{position}" class="hideInProfile"/>
	</xsl:otherwise>
      </xsl:choose>
    </h4>
    <!--Showing region of interest-->
    <p class="ROI"><code><br />
      <!--xsl:value-of select="regionOfInterest"/-->
      <xsl:call-template name="color-dna">
	<xsl:with-param name="dna" select="regionOfInterest" />
      </xsl:call-template>
    </code></p>
    <!--Defining allele stats div-->
    <div class="allele-stats {$locusName}">
      <h5>Allele stats</h5>
      <xsl:value-of select="@direction-distrib"/> strand distribution.<br />
      <xsl:if test="/results/@flankedOut = 'True'">
	<xsl:value-of select="qualityFlanks/@clean"/> clean flanks;
	<xsl:if test="/results/@homomerCorrection = 'True'">
	  <xsl:value-of select="qualityFlanks/@clean_compressed"/> flanks with homopolymer issues; and
	</xsl:if>
	<xsl:value-of select="qualityFlanks/@unclean"/> unclean flanks.
      </xsl:if>
    </div>

    <!--Defining relation div-->
    <div class="relations {$locusName}">
      <h5>Relations to other sequences within <xsl:value-of select="$locusName"/> &#8594; <xsl:value-of select="count(cluster-info/differences/rel)"/> in total</h5>
      <!--xsl:if test="cluster-info/differences"-->
      <xsl:for-each select="cluster-info/differences">
	<xsl:number value="@amount" format="I"/>'th degree relation indices &#8594;
	<!--xsl:value-of select="string-join(rel/@index, ',&#x20;'"/-->
	<xsl:for-each select="rel">
             <xsl:value-of select="@index" />
             <xsl:if test="position() != last()">,&#x20;</xsl:if>
	</xsl:for-each>
	<br />
      </xsl:for-each>
       <!--TODO <button type="button" id="alignmentbutton" class="{$locusName}" onclick="">View alignment with relatives</button-->
    </div>
  </xsl:template>

  <xsl:template name="javascript">
    <script>
       /*Hide all hiddenCandidates after page has loaded*/
       $('div.hiddenCandidate').toggle()
       
       function withinLocusAlignment() { /*Change this to make the relations alignment,
       should take locus and indices of relations as argument, and do everything with toggle*/
         $('div.alleleCandidate').each( function() {
	   if( $('h4 input',this).is(':checked') ) {
	     $(this).show()
	   }
	   else {
	     $(this).hide()
	   }
	 } )
	 $('.allele-stats').hide();
	 $('.relations').hide();
	 $('.hideInProfile').hide()
       }

       function processLoci() {
	 $(this).data('clicked',!$(this).data('clicked'));
	 if ($(this).data('clicked')) {
           $('div.alleleCandidate').each( function() {
	     if( $('h4 input',this).is(':checked') ) {
	       $(this).show()
	     }
	     else {
	       $(this).remove()
	     }
	   } )
           $('.alleleCandidate').css('min-height',"60px");
	   $('.alleleCandidate').css('border-bottom-style',"none");
	   $('.allele-stats').remove();
	   $('.relations').remove();
	   $('.hideInProfile').remove();
           $('.alleleCandidates,.locusHeader').css('border','1px dotted black')
	   $('.locusHeader').css('border-bottom','none')
	   $('.alleleCandidates').css('width','900')
	   
	   var html = $('html').clone();
	    html.find('#profileButton').remove()
	   html.find('head').append('<title>MyFLq Processed Profile</title>');
	   html.find('div.resultMyFLq').css('width','900px');
	   var htmlString = html.html();

	   window.open("data:text/html;charset=utf-8,<html>"+htmlString+"</html>");
	   /*window.open("data:text/html;charset=utf-8,"+escape( htmlString ))
	   /*window.open("data:text/html;base64,"+btoa(unescape(encodeURIComponent( htmlString ))))
	   /*var profileWindow = window.open("","_blank")
	   /*profileWindow.document.write(htmlString)
	   /*profileWindow.document.title("MyFLq processed profile")*/
	   
	   $('#profileButton').html('Restart')
         }
	 else {
           /*$('.alleleCandidate').css('min-height',"175px")*/
	   location.reload();
         }
       }
    </script>
  </xsl:template>

  <!--Functions-->
  <xsl:template name="add-whitespace">
    <xsl:param name="i"/>
    <xsl:param name="str"/>
    <xsl:param name="where" select="before"/>
    <xsl:choose>
      <xsl:when test="$i > 0">
	<xsl:call-template name="add-whitespace">
	  <xsl:with-param name="i" select="$i - 1"/>
	  <xsl:with-param name="str" select="concat($str,'&#160;')"/><!--TODO add logic for where-->
	  <xsl:with-param name="where" select="$where"/>
	</xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
	<code><xsl:value-of select="$str"/></code>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="color-dna">
    <xsl:param name="dna"/>

    <xsl:if test="string-length($dna) &gt; 0">
      <span class="{substring($dna, 1, 1)}"><xsl:value-of select="substring($dna, 1, 1)"/></span>
      <!--xsl:if test="(string-length($dna) mod 80) = 0"><wbr/></xsl:if-->
      <xsl:call-template name="color-dna">
	<xsl:with-param name="dna" select="substring($dna, 2)"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
  
  <!--xsl:template name="string-join">
  Not working yet!
    <xsl:param name="strings"/>
    <xsl:param name="separator" select="&#x20;"/>
    <xsl:choose>
      <xsl:when test="boolean($addString)">

      </xsl:when>
      <xsl:otherwise>
	<xsl:call-template name="string-join">
	  <xsl:with-param name="" select="$i - 1"/>
	  <xsl:with-param name="str" select="concat($str,'&#160;')"/>
	  <xsl:with-param name="where" select="$where"/>
	</xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
    
  </xsl:template-->

</xsl:stylesheet>
