var get_data = function(){
  var r = 200;
  var cy = 300;
  var cx = 300;
  var height = 600;

  var svg = d3.select("#viz");
  var trash_x1 = 0;
  var trash_x2 = 40;
  var trash_y1 = 0;
  var trash_y2 = 40;

  var dragend = function dragend(d){

    var item = d3.select(this);
      if((item.attr('x') < trash_y2) && (item.attr('y') < trash_x2)){
        item.remove();
      }

    $.get('/titles', function(data){

      var titles = d3.selectAll('p').data(data).transition()
            .text(function(d){return d;});
    }
         );
  };
    
  var dragmove = function dragmove(d) {
    var word = d3.select(this)
            .attr("y", d3.event.y)
          .attr("x", d3.event.x);
    
    if((d3.event.y < trash_y2) && (d3.event.x < trash_x2)){
      
      word.style('stroke', 'red');}
      else{
        word.style('stroke', 'black');
      }
  };
  
  $.get('/data', function(response) {

    var data = response.authors;
    var titles = response.titles;
    
    var num_words = data.length;

    var scale = d3.scale.linear()
          .domain([0, num_words/2])
          .range([0,height]);
    
    var text = d3.select('#viz').selectAll('text').data(data).enter()
      .append('text')
          .text(function(d) {return d;})
          .style("stroke", "black")
      .attr('x', function(d, i){
        
        var angle = Math.sin(2*(i / num_words)*Math.PI);
        //var offset = 50*Math.sin(2*(i / num_words)*Math.PI);

        if( i > num_words /2 ){
          var offset = 50;
          
        }else{
            var offset = 0;
          }
        return r*angle + cx;})
    
      .attr('y', function(d, i){

        var pos = i;
        if( i > num_words/2){
          pos = pos - (num_words/2);
        }
        
        return scale(pos) + 10;})
          .style('cursor', 'grabbing');


  
    
    var drag = d3.behavior.drag().on('drag', dragmove)
          .on('dragend', dragend);

    text.call(drag);

    // Do the other paper titles
    var pap_div = d3.select("#papers");

    pap_div.selectAll('p').data(titles).enter().append('p')
      .text(function(d){return d;});

    
  }
       );
};
