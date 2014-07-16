function draw(error,data,width,height) {
    "use strict";

    //Set defaults
    width = width || 900; 
    height = height || 400;

    //Prepare data
    var results = data.documentElement;
    if (results.nodeName != "results"){
	results = results.getElementsByTagName("results")[0];
      //.getElementsByTagName("results") is a hack to allow processing 
      //when html document is passed instead of xml data to draw
      //this is used in the BaseSpace version, where the xml is dumped into
      //the html document
    }
    if (results.getElementsByTagName("lociDatabaseState").length){
	//Database info also contains locus tags, 
	//and therefore needs to be removed if present
	try {
	    results.getElementsByTagName("lociDatabaseState")[0].remove();
	}
	catch(err) {
	    results.removeChild(results.getElementsByTagName("lociDatabaseState")[0]);
	}
    }

      //Normal sequential graph
    var lociNames = [];
    var lociStartPosition = [0]; //First locus starts at 0
    //var lociInfo = {}
    var loci = results.getElementsByTagName("locus");
    for (var i=0;i<loci.length;i++)
	{
	    lociNames[lociNames.length] = loci[i].getAttribute('name');
	    lociStartPosition[lociStartPosition.length] = lociStartPosition[lociStartPosition.length-1] + loci[i].getElementsByTagName('alleleCandidate').length + 1;
	}

      //Graph with alleles sorted on length
    var stackedGraph = false,
        stackedAlleles = [],
        stackedAllelesLociPositions = [0];

    for (var i=0;i<loci.length;i++) {
	var alleles = loci[i].getElementsByTagName('alleleCandidate'),
	    rangeL = [],
	    abundances = [];
	for (var j=0;j<alleles.length;j++) {
	    var roi = alleles[j].getElementsByTagName('regionOfInterest')[0].textContent;
	    rangeL[rangeL.length] = (roi == "[RL]") ? 0 : roi.length;
	    abundances[abundances.length] = parseFloat(alleles[j].getAttribute('abundance'));
	}
	var amin = Math.min.apply(Math, rangeL),
	    amax = Math.max.apply(Math, rangeL);
	//smallestLocusAllele[smallestLocusAllele.length] = amin;
	var locusStart = stackedAllelesLociPositions[stackedAllelesLociPositions.length-1];
	stackedAllelesLociPositions[stackedAllelesLociPositions.length] = locusStart + amax - amin + 1; //locusEnd
	for (var j=0;j<alleles.length;j++) {
	    stackedAlleles[stackedAlleles.length] = [
		rangeL[j] - amin + locusStart,
		abundances[j],
		(j == 0 || rangeL[j] != rangeL[j-1]) ? 100 : stackedAlleles[stackedAlleles.length-1][2] - abundances[j-1] - 0.5
	    ]; // 0.5 => to separate the stacked bars with a certain distance
	}
    }

    //Prepare chart
      //svg properties
    var margin = {top: 30, right: 30, bottom: 70, left: 40},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;
    
      //Setting scales
    var domainMaxNormalGraph = [0,loci.length + results.getElementsByTagName("alleleCandidate").length],
        domainMaxStackedGraph = [-1,stackedAllelesLociPositions[stackedAllelesLociPositions.length-1]+1];
    var x_scale = d3.scale.linear().range([0,width])
        .domain(domainMaxNormalGraph);
        /*x_stackedScale = d3.scale.linear().range([0,width])
        .domain([0,stackedAllelesLociPositions[stackedAllelesLociPositions.length-1]]);*/
    var x_axis = d3.svg.axis().scale(x_scale).tickValues(lociStartPosition)
	.tickFormat(function(d) { return lociNames[lociStartPosition.indexOf(d)];});
    var axisText_dx = ".8em",
        axisText_dy = "-.05em";
    var y_scale = d3.scale.linear().range([height,0])
        .domain([0,100]);
    var y_axis = d3.svg.axis().scale(y_scale).orient("left");
    function barWidth() {
	return Math.max(1,x_scale(1)-x_scale(0)-1);
	//return (stackedGraph) ?  Math.max(1,x_stackedScale(1)-1) : Math.max(1,x_scale(1)-1);
    }
    //console.log(x_extent,barWidth);

    //Constructing chart
    var sampleName = (results.getAttribute("sample")) ? results.getAttribute("sample") : "unknown";
    var date = new Date(results.getAttribute("timestamp")*1000);
    d3.select("#sampleTitle").append("h1")
	.text("Sample " +
	      sampleName +
	      ", processed " +
	      date);
    var svg = d3.select("#svgContainer")
        .append("svg")
          .attr("width",width + margin.left + margin.right)
          .attr("height",height + margin.top + margin.bottom)
        .append("g")
          .attr("transform","translate(" + margin.left + "," + margin.top + ")");

    var maxPosStackedBar = stackedAllelesLociPositions[stackedAllelesLociPositions.length-1];
    var zoom = d3.behavior.zoom()
        .x(x_scale)
	.scaleExtent([.9,Math.min(100,Math.max(10,10*maxPosStackedBar/width))]) //simple [1,10]
        .on("zoom", zoomHandler);

    //Clipping zone for all bars and x axis
    d3.select("#svgContainer svg")
        .append("defs")
	.append("clipPath")
	 .attr("id", "clip")
	.append("rect")
	  .attr("x", 0)
	  .attr("y", 0)
	  .attr("width", width)
	  .attr("height", height + margin.bottom);
    var bars = svg.append("g").attr("clip-path", "url(#clip)")

    svg.append("g")
          .attr("class","x axis")
          .attr("clip-path", "url(#clip)")
          .attr("transform","translate(0,"+height+")")
        .call(x_axis)
        .selectAll("text")  
          .style("text-anchor", "start")
          .attr("dx", axisText_dx)
          .attr("dy", axisText_dy)
          .attr("transform", "rotate(45)");
    /*d3.select(".x.axis")
      .append("text")
        .text("Loci")
        .attr("x",(width/2)-margin.left)
        .attr("y",margin.bottom/1.5)*/;

    svg.append("g")
          .attr("class","y axis")
          //.attr("transform","translate("+margin+",0)")
        .call(y_axis);
    d3.select(".y.axis")
      .append("text")
      .text("Abundance (%)")
      .attr("transform","rotate(-90,-43,0) translate(-200,"+(margin.left/2)+")");

    svg.append("rect")
	  .attr("class", "pane")
	  .attr("width", width)
	  .attr("height", margin.bottom) //Zoom functionality only accessible on x-axis
	  .attr("y", height)
	.call(zoom);//.on("dblclick.zoom",null);

    bars.selectAll("g.locus")
        .data(results.getElementsByTagName("locus"))
        .enter()
        .append("g")
          .attr("class","locus")
        .selectAll("rect")
        .data(function(d) { return d.getElementsByTagName("alleleCandidate"); })
        .enter()
        .append("rect")
          .attr("class","alleleCandidate")
	  .attr("id", function(d,i) {
	      return d.parentNode.getAttribute("name")+"_"+i;
	      })
          .attr("width",barWidth())
          .attr("height",function(a) { return height - y_scale(parseFloat(a.getAttribute('abundance')))})
          .attr("transform",function(a,i) {  return "translate("+x_scale(lociStartPosition[lociNames.indexOf(a.parentNode.getAttribute("name"))]+i)+","+y_scale(parseFloat(a.getAttribute('abundance')))+")"})
          .style("fill",function(a) { return (a.getAttribute("db-name") == "NA") ? "red": "green";})
          //.text(function(a) { return a.getAttribute('db-name'); })

    function zoomHandler() {
	d3.select("#dbnameTip").remove();
	svg.select(".x.axis").call(x_axis)
	      .selectAll("text")  
              .style("text-anchor", "start")
              .attr("dx", axisText_dx)
              .attr("dy", axisText_dy);
	//svg.select(".y.axis").call(y_axis);
	if (stackedGraph) {
	    bars.selectAll(".alleleCandidate")
		  .attr("width",barWidth())
		  .attr("transform", function(d,i) { return "translate("+x_scale(stackedAlleles[i][0]) + "," + (y_scale(stackedAlleles[i][1])-y_scale(stackedAlleles[i][2]))+")";});
	}
	else {
	    bars.selectAll("g.locus")
		.selectAll("rect.alleleCandidate")
       		  .attr("width",barWidth())
		  .attr("transform", function(d,i) { return "translate(" + x_scale(lociStartPosition[lociNames.indexOf( d.parentNode.getAttribute("name"))]+i) + "," + y_scale(parseFloat(d.getAttribute('abundance')))  + ")";});
	}
    }

    //Bar mouseover functionality
    var relationDegrees = ["I'st","II'nd"];
    svg.selectAll(".alleleCandidate")
	.on("mouseover.tooltip", function(d,i) {
	    d3.select("#dbnameTip").remove();
	    d3.select("#alleleInfo").remove();
	    var x_pos = (stackedGraph) ? stackedAlleles[i][0] :
		lociStartPosition[lociNames.indexOf(this.id.split('_')[0])] + Number(this.id.split('_')[1]);
	    //var y_pos =
	    svg.append("text")
		.text(d.getAttribute("db-name") +
		      ( (d.getAttribute("db-subtype")) ? d.getAttribute("db-subtype") : "" )  )
		.attr("id","dbnameTip")
	        .attr("x", x_scale(x_pos))
		.style("text-anchor", "middle");

	    //Allele info div
	    var aI = d3.select("#chart")
		.append("div")
		  .attr("id","alleleInfo");
	    var locus = d.parentNode;
	    aI.append("h2")
		.text("Locus "+locus.getAttribute("name")+
		      " → allele candidate: "+d.getAttribute("db-name")+
		     ( (d.getAttribute("db-subtype")) ? d.getAttribute("db-subtype") : "" )  );
	    var table = aI.append("table");
	    var row = table.append("tr");
	    row.append("td").text("Locus stats")
		.attr("colspan",2)
		.attr("style","border-width:1px; border-bottom-style: solid; border-right-style: solid;");
	    row.append("td").text("Allele stats")
		.attr("colspan",2)
		.attr("style","border-width:1px; border-bottom-style: solid;");
	    row = table.append("tr");
	    row.append("td").text("Total reads");
	    row.append("td").text(locus.getAttribute("reads")).attr("style","border-width:1px; border-right-style: solid;");
	    row.append("td").text("Index");
	    row.append("td").text(d.getElementsByTagName('cluster-info')[0].getAttribute("index"));
	    row = table.append("tr");
	    row.append("td").text("Filtered reads");
	    row.append("td").text(locus.getAttribute("readsFiltered"))
		.attr("style","border-width:1px; border-right-style: solid;");
	    row.append("td").text("Abundance");
	    row.append("td").text(d.getAttribute("abundance"));
	    row = table.append("tr");
	    row.append("td").text("Total unique");
	    row.append("td").text(locus.getAttribute("uniqueReads"))
		.attr("style","border-width:1px; border-right-style: solid;");
	    row.append("td").text("Strand distribution");
	    row.append("td").text(d.getAttribute("direction-distrib"));
	    row = table.append("tr");
	    row.append("td").text("Filtered unique");
	    row.append("td").text(locus.getAttribute("uniqueFiltered"))
		.attr("style","border-width:1px; border-right-style: solid;");
	    row.append("td").text("Clean flanks");
	    row.append("td").text(d.getElementsByTagName("qualityFlanks")[0].getAttribute("clean"));

	    //In profile checkbox
	    aI.append("br")
	    aI.append("label")
		.attr("for","profileCheckbox")
		.text("In profile: ");
	    var profileCB = aI.append("input")
		.attr("type","checkbox")
		.attr("id","profileCheckbox");
	    if (parseFloat(d.getAttribute('abundance')) < threshold) {
		profileCB.attr("disabled","disabled");
	    } else if (d.getAttribute('profile')!='no') {
		profileCB.attr("checked","checked");
	    }
	    profileCB.on("click",function(){
		//console.log(this);
		d.setAttribute('profile', (d.getAttribute('profile')=='no') ? 'yes' : 'no');
	    })
window.pcb = profileCB;//DEBUG

	    //Cluster-info
	    aI.append("h3").text("Relations to other sequences within "+locus.getAttribute("name"));
	    table = aI.append("div").attr("style","overflow-x: scroll;").append("table");
	    row = table.append("tr");
	    row.append("td").text("Allele index")
		.attr("style","border-width:1px; border-bottom-style: solid; border-right-style: solid;");
	    row.append("td").text("Relation degree")
		.attr("style","border-width:1px; border-bottom-style: solid; border-right-style: solid;")
	    row.append("td").text("Sequence")
		.attr("style","border-width:1px; border-bottom-style: solid;");
	    var clusterInfo = d.getElementsByTagName('cluster-info')[0];
	    row = table.append("tr");
	    row.append("td").text(clusterInfo.getAttribute("index"))
		.attr("style","border-width:1px; border-bottom-style: solid; border-right-style: solid;");
	    row.append("td").text("-")
		.attr("style","border-width:1px; border-bottom-style: solid; border-right-style: solid;");
	    row.append("td").call(colorizeDNA, d.getElementsByTagName('regionOfInterest')[0].textContent)
		.attr("style","border-width:1px; border-bottom-style: solid; font-family: monospace;");

	    //Retrieving connection
	    var differences = clusterInfo.getElementsByTagName("differences");
	    for (var i=0; i < differences.length; i++) {
		var relations = differences[i].getElementsByTagName("rel");
		for (var j=0; j < relations.length; j++) {
		    var relation = locus.getElementsByTagName("alleleCandidate")[Number(relations[j].getAttribute("index"))-1]
		    row = table.append("tr");
		    row.append("td").text(relations[j].getAttribute("index"))
			.attr("style","border-width:1px; border-right-style: solid;");
		    row.append("td").text(relationDegrees[Number(differences[i].getAttribute("amount")-1)])
			.attr("style","border-width:1px; border-right-style: solid;");
		    row.append("td").call(colorizeDNA, relation.getElementsByTagName('regionOfInterest')[0].textContent)
			.attr("style","border-width:1px; font-family: monospace;");
		}
	    }
	})
    svg.selectAll(".alleleCandidate")
	.on("click", function(d,i) {
	    if (parseFloat(d.getAttribute('abundance')) >= threshold)
	    {
		d.setAttribute('profile', (d.getAttribute('profile')=='no') ? 'yes' : 'no');
		//Set profile checkbox accordingly
		d3.select("#profileCheckbox")
		    .attr("checked", (d.getAttribute('profile')=='no') ? null : 'checked');
	    }
	})

    //Threshold functionality
    var gradient = d3.select("svg defs").append("linearGradient")
        .attr("id", "gradient")
	.attr("x2", "0%")
	.attr("y2", "100%");

    gradient.append("stop")
	.attr("offset", "0%")
	.attr("stop-color", "#fff")
	.attr("stop-opacity", .5);
    
    gradient.append("stop")
	.attr("offset", "100%")
	.attr("stop-color", "#999")
	.attr("stop-opacity", 1);

    var threshold = 10; //%
    var drag = d3.behavior.drag()
	//.origin(function(d) { return d; })
	.on("drag", dragmove);

    svg.append("rect")
	.attr("class","threshold")
	.attr("x",0)
	.attr("y",y_scale(threshold))
	.attr("width",width)
	.attr("height",y_scale(0)-y_scale(threshold))
	.style("fill", "url(#gradient)")
	.call(drag);

    function dragmove(d) {
	var newThreshold = Math.max(0, Math.min(100, y_scale.invert(d3.event.y)));
	d3.select(this)
	    .attr("y",y_scale(newThreshold))
	    .attr("height",y_scale(0)-y_scale(newThreshold));
	threshold = newThreshold.toFixed(2);
	d3.selectAll(".thresQuant").property("value",threshold);
    }

    d3.selectAll(".thresQuant").on("change",function(){
	threshold = parseFloat(d3.select(this).property("value"));
	d3.select("rect.threshold")
	    .attr("y",y_scale(threshold))
	    .attr("height",y_scale(0)-y_scale(threshold));
	d3.selectAll(".thresQuant").property("value",threshold);
    })

    //Transition to sorted stacked alleles
    d3.select("#sortLength")
	.on("click", function() {
	    d3.select("#dbnameTip").remove();
	    var checkbox = d3.select(this);
	    if (checkbox.property("checked")) {
		//Transforming graph
		stackedGraph = true;
		x_scale.domain(domainMaxStackedGraph);
		zoom.x(x_scale); //otherwise zoom functionality seems to have issues
		//x_axis.scale(x_stackedScale).tickValues(stackedAllelesLociPositions)
		x_axis.tickValues(stackedAllelesLociPositions)
		    .tickFormat(function(d) { return lociNames[stackedAllelesLociPositions.indexOf(d)];});
		
		/*var transition = svg.transition().duration(750),*/
		var delay = function(d, i) { return i * 50; };

		bars.selectAll(".alleleCandidate")
		    //.data(results.getElementsByTagName("alleleCandidate"))
		    .transition()
		    .delay(delay)
		    .attr("width",barWidth())
		    .attr("transform",function(d,i) {  return "translate("+x_scale(stackedAlleles[i][0]) + "," + (y_scale(stackedAlleles[i][1])-y_scale(stackedAlleles[i][2]))+")"});

//		window.sa = stackedAlleles;

		svg.select(".x.axis")
		    .transition()
		    //.delay(delay)
		    .duration(1000)
		    .call(x_axis)
		    .each("start", function() {
			d3.select(this)
			//d3.select(".x.axis")
			    .selectAll("text")
			    .style("text-anchor", "start")
			    .attr("dx", axisText_dx)
			    .attr("dy", axisText_dy)
			    .attr("transform", "rotate(45)");
			//console.log(this);
		    });
		
		//Hide threshold
		d3.select(".threshold")
		    .attr("visibility", "hidden");
	    }
	    else {
		stackedGraph = false;
		d3.select(".threshold")
		    .attr("visibility", "visible");
		x_scale.domain(domainMaxNormalGraph);
		zoom.x(x_scale); //otherwise zoom functionality seems to have issues
		x_axis.tickValues(lociStartPosition)
		    .tickFormat(function(d) { return lociNames[lociStartPosition.indexOf(d)];});
		svg.select(".x.axis")
		    .call(x_axis)
		    .selectAll("text")
		    .style("text-anchor", "start")
		    .attr("dx", axisText_dx)
		    .attr("dy", axisText_dy)
		    .attr("transform", "rotate(45)");
		bars.selectAll("g.locus")
		    .selectAll("rect.alleleCandidate")
		      .attr("transform", function(d,i) { return "translate(" + x_scale(lociStartPosition[lociNames.indexOf( d.parentNode.getAttribute("name"))]+i) + "," + y_scale(parseFloat(d.getAttribute('abundance')))  + ")";});
	    }	
	})

    //Make profile
    d3.select("#makeProfile")
	.on("click", function() {
	    //First create profile in memory
	    var multipleContributor = false;
	    var profileHTML = document.createElement("html");
	    var docRoot = d3.select(profileHTML).append("body").append("div");
	    docRoot.append("h2").text( "Processed profile from " +
				       sampleName +
				       ", with threshold: " +
				       threshold + "%"
				     );
	    var table = docRoot.append("table");
	    var row = table.append("tr");
	    row.append("td").text("Locus")
		.attr("style","border-width:1px; border-bottom-style: solid; border-right-style: solid;");
	    row.append("td").text("Alleles")
		.attr("style","border-width:1px; border-bottom-style: solid;");

	    //Form for calculating profile stat
	    var form = docRoot.append("form")
		.attr("action","http://strbase.org/calc.php")
		.attr("method","post");
	    form.append("input").attr("name","mode").attr("type","hidden").attr("value","check");
	    form.append("input").attr("name","fst").attr("type","hidden").attr("value","0.01");
	    form.append("input").attr("name","countryselect[DB]").attr("type","hidden").attr("value","Full database");
	    var strBaseLoci = { 'D3S1358' : 'd3',
				'vWA' : 'vwa',
				'D16S539' : 'd16',
				'D8S1179' : 'd8',
				'D21S11' : 'd21',
				'D18S51' : 'd18',
				'TH01' : 'th01',
				'FGA' : 'fga'
		}

	    //Add all loci
	    d3.selectAll(".locus").each(function(d,i){
		row = table.append("tr");
		row.append("td").text(d.getAttribute("name")).attr("style","border-width:1px; border-right-style: solid;");
		//Retrieve alleles that passed the threshold
		var alleles = []
		var sBA = false; //This becomes true when first allele is ready to be submitted, maximum two allowed
		for (var j = 0; j < d.getElementsByTagName('alleleCandidate').length; j++) {
		    var aC = d.getElementsByTagName('alleleCandidate')[j];
		    if ( parseFloat(aC.getAttribute('abundance')) >= threshold &
			 aC.getAttribute('profile')!='no') {
			alleles[alleles.length] = aC.getAttribute("db-name") +
			    ( (aC.getAttribute("db-subtype")) ? aC.getAttribute("db-subtype") : "" );
		    
			//Add allele candidate to form if in strBaseLoci
			if (d.getAttribute("name") in strBaseLoci && aC.getAttribute("db-name") != 'NA'){
			    form.append("input").attr("name","inputsys["+strBaseLoci[d.getAttribute("name")]+"]["+String(sBA+1)+"]")
				.attr("type","hidden").attr("value",aC.getAttribute("db-name"));
			    sBA = true;
			}
		    }
		}
		if (alleles.length > 2) {multipleContributor = true}
		row.append("td").text(alleles.join());
		//console.log(i);
	    });

	    if (multipleContributor) {
		d3.select(profileHTML).select("div").append("p")
		    .text("Based on the threshold, this sample derives from multiple contributors.")
		    .attr("style","color:red;");
		d3.select(profileHTML).select("form").remove();
	    }
	    else {
		form.append("br");
		form.append("input").attr("type","submit").attr("value","Calculate probability on ENFSI");
		form.append("p").text("(This only calculates the probability for the subset of ENFSI loci.)");
	    }

	    var profileWindow = window.open("data:text/html;charset=utf-8,<html>"+d3.select(profileHTML).html()+"</html>");//,"Profile","location=no");
	    //var profileWindow = window.open('');
	    //var profileRoot = d3.select(profileWindow.document.body);
	})

}

function colorizeDNA(selection,dna) {
    var colors = { 'A': 'red',
		   'C': 'green',
		   'T': 'orange',
		   'G': 'green'
		 };
    for (var i=0; i < dna.length; i++) {
	selection.append("span").attr("style","color: "+colors[dna.charAt(i)]+";").text(dna.charAt(i));
    }
}
