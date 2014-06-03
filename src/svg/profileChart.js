function draw(data) {
    "use strict";

    //Prepare data
    var lociNames = []
    var lociStartPosition = [0] //First locus starts at 0
    //var lociInfo = {}
    var loci=data.documentElement.getElementsByTagName("locus");
    for (var i=0;i<loci.length;i++)
	{
	    lociNames[lociNames.length] = loci[i].getAttribute('name');
	    lociStartPosition[lociStartPosition.length] = lociStartPosition[lociStartPosition.length-1] + loci[i].getElementsByTagName('alleleCandidate').length + 1;
	}

    //svg properties
    var margin = {top: 10, right: 30, bottom: 70, left: 40},
    width = 900 - margin.left - margin.right, //will be dynamically set, based on number of alleles
    height = 400 - margin.top - margin.bottom;
    
    //Setting scales
    //var x_extent = d3.extent(data.documentElement.getElementsByTagName("locus"),function(d){return Number(d.getAttribute("reads"))});
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
    var ch = d3.select("#chart")
        .append("svg")
          .attr("width",width + margin.left + margin.right)
          .attr("height",height + margin.top + margin.bottom)
        .append("g")
          .attr("transform","translate(" + margin.left + "," + margin.top + ")");
    
    ch.append("g")
          .attr("class","x axis")
          .attr("transform","translate(0,"+height+")")
        .call(x_axis)
        .selectAll("text")  
          .style("text-anchor", "start")
          .attr("dx", ".8em")
          .attr("dy", ".15em")
          .attr("transform", "rotate(45)");
    d3.select(".x.axis")
      /*.append("text")
        .text("Loci")
        .attr("x",(width/2)-margin.left)
        .attr("y",margin.bottom/1.5)*/;

    ch.append("g")
          .attr("class","y axis")
          //.attr("transform","translate("+margin+",0)")
        .call(y_axis);
    d3.select(".y.axis")
      .append("text")
      .text("Abundance (%)")
      .attr("transform","rotate(-90,-43,0) translate(-200,"+(margin.left/2)+")");

    ch.selectAll("g.locus")
        .data(data.documentElement.getElementsByTagName("locus"))
        .enter()
        //.append("div")
        .append("g")
          .attr("class","locus")
        //.style("float","left")
        //.style("height","50px")
        //.style("width",function(d) { return d.getElementsByTagName("alleleCandidate").length * 10 + "px"; })
        //.text(function(d) { return d.getAttribute('name'); })
        //.selectAll("div")
        .selectAll("rect")
        .data(function(d) { return d.getElementsByTagName("alleleCandidate"); })
        .enter()
        //.append("div")
        .append("rect")
          .attr("class","alleleCandidate")
          .attr("width",barWidth)
          .attr("height",function(a) { return height - y_scale(parseFloat(a.getAttribute('abundance')))})
          .attr("transform",function(a,i) {  return "translate("+x_scale(lociStartPosition[lociNames.indexOf(a.parentElement.getAttribute("name"))]+i)+","+y_scale(parseFloat(a.getAttribute('abundance')))+")"})
          .style("fill",function(a) { return (a.getAttribute("db-name") == "NA") ? "red": "green";})
          //.text(function(a) { return a.getAttribute('db-name'); })
}
