function draw(data) {
    "use strict";

    //Prepare data
    var lociNames = [];
    var lociStartPosition = [0]; //First locus starts at 0
    //var lociInfo = {}
    var loci=data.documentElement.getElementsByTagName("locus");
    for (var i=0;i<loci.length;i++)
	{
	    lociNames[lociNames.length] = loci[i].getAttribute('name');
	    lociStartPosition[lociStartPosition.length] = lociStartPosition[lociStartPosition.length-1] + loci[i].getElementsByTagName('alleleCandidate').length + 1;
	}

    //svg properties
    var margin = {top: 30, right: 30, bottom: 70, left: 40},
    width = 900 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;
    
    //Setting scales
    var x_extent = [0,loci.length + data.documentElement.getElementsByTagName("alleleCandidate").length]
    var x_scale = d3.scale.linear().range([0,width])
        .domain(x_extent);
    var x_axis = d3.svg.axis().scale(x_scale).tickValues(lociStartPosition)
	.tickFormat(function(d) { return lociNames[lociStartPosition.indexOf(d)];});
    var y_scale = d3.scale.linear().range([height,0])
        .domain([0,100]);
    var y_axis = d3.svg.axis().scale(y_scale).orient("left");
    var barWidth = x_scale(1)-1;
    //console.log(x_extent,barWidth);

    //Constructing chart
    var svg = d3.select("#chart")
	  .attr("width",width + margin.left + margin.right)
        .append("svg")
          .attr("width",width + margin.left + margin.right)
          .attr("height",height + margin.top + margin.bottom)
        .append("g")
          .attr("transform","translate(" + margin.left + "," + margin.top + ")");

    var zoom = d3.behavior.zoom()
        .x(x_scale)
        .scaleExtent([1,10])
        .on("zoom", zoomHandler);

    //Clipping zone for all bars and x axis
    d3.select("#chart svg")
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
          .attr("dx", ".8em")
          .attr("dy", "-.05em")
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
        .data(data.documentElement.getElementsByTagName("locus"))
        .enter()
        .append("g")
          .attr("class","locus")
        .selectAll("rect")
        .data(function(d) { return d.getElementsByTagName("alleleCandidate"); })
        .enter()
        .append("rect")
          .attr("class","alleleCandidate")
	  .attr("id", function(d,i) {
	      return d.parentElement.getAttribute("name")+"_"+i;
	      })
          .attr("width",barWidth)
          .attr("height",function(a) { return height - y_scale(parseFloat(a.getAttribute('abundance')))})
          .attr("transform",function(a,i) {  return "translate("+x_scale(lociStartPosition[lociNames.indexOf(a.parentElement.getAttribute("name"))]+i)+","+y_scale(parseFloat(a.getAttribute('abundance')))+")"})
          .style("fill",function(a) { return (a.getAttribute("db-name") == "NA") ? "red": "green";})
          //.text(function(a) { return a.getAttribute('db-name'); })

    function zoomHandler() {
	d3.select("#dbnameTip").remove();
	svg.select(".x.axis").call(x_axis)
	      .selectAll("text")  
              .style("text-anchor", "start")
              .attr("dx", ".8em")
              .attr("dy", ".15em");
	//svg.select(".y.axis").call(y_axis);
	bars.selectAll("g.locus")
	    .selectAll("rect.alleleCandidate")
              .attr("clip-path", "url(#clip)")
	      .attr("transform", function(a,i) { return "translate(" + x_scale(lociStartPosition[lociNames.indexOf( a.parentElement.getAttribute("name"))]+i) + "," + y_scale(parseFloat(a.getAttribute('abundance')))  + ") scale(" + d3.event.scale + ", 1)";});
    }

    //Mouseover label
    svg.selectAll(".alleleCandidate")
	.on("mouseover.tooltip", function(d) {
	    d3.select("#dbnameTip").remove();
	    var x_pos = lociStartPosition[lociNames.indexOf(this.id.split('_')[0])] + Number(this.id.split('_')[1]);
	    var y_pos =
	    svg.append("text")
		.text(d.getAttribute("db-name"))
		.attr("id","dbnameTip")
	        .attr("x", x_scale(x_pos));
	    //console.log(this);
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
	threshold = newThreshold;
    }

    //Transition to graph with alleles sorted on length
    var stackedAlleles = []
    var stackedAllelesLociPositions = [0]
    //var smallestLocusAllele = []
    d3.select("#sortLength")
	.on("click", function() {
	    var checkbox = d3.select(this);
	    if (checkbox.property("checked")) {
		//Preparing data
		if (stackedAlleles.length == 0) {
		    for (var i=0;i<loci.length;i++) {
			var alleles = loci[i].getElementsByTagName('alleleCandidate');
			var rangeL = [];
			var abundances = [];
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
				(j == 0 || rangeL[j] != rangeL[j-1]) ? abundances[j] : stackedAlleles[stackedAlleles.length-1][1] + abundances[j] + 0.5
			    ]; // 0.5 => to separate the stacked bars with a certain distance
			}
		    }
		}
		//Transforming graph
		var x0 = x_scale.domain([0,stackedAllelesLociPositions[stackedAllelesLociPositions.length]]).copy();
		x_axis.scale(x_scale).tickValues(stackedAllelesLociPositions)
		    .tickFormat(function(d) { return lociNames[stackedAllelesLociPositions.indexOf(d)];});
		
		var transition = svg.transition().duration(750),
		delay = function(d, i) { return i * 50; };

		transition.selectAll(".alleleCandidate")
		    .delay(delay)
		    .attr("width", Math.max(1,x_scale(1)))
		    .attr("x", function(d,i) {  return x0(stackedAlleles[i][0])});
		    /*.attr("transform",function(d,i) {  return "translate("+x_scale(stackedAlleles[i][0]) + "," + y_scale(stackedAlleles[i][1])+")"})*/

		transition.select(".x.axis")
		    .call(x_axis)
		    .selectAll("text")  
		    .style("text-anchor", "start")
		    .attr("dx", ".8em")
		    .attr("dy", "-.05em")
		    .attr("transform", "rotate(45)");
		    /*.selectAll("g")
		    .delay(delay);*/

		/*d3.select(".x.axis").call(x_axis);
		/*d3.select(".alleleCandidate")
		    .transition()
		    .duration(500)
		    .attr("width",x_scale(1))
		    .attr("transform",function(d,i) {  return "translate("+x_scale(stackedAlleles[i][0]) + "," + y_scale(x_scale(stackedAlleles[i][1]))+")"});*/
	    }
	    else {
		console.log("not")
	    }	
	})

}
