var get_data = function(){
  var r = 200;
  var cy = 300;
  var cx = 300;
  var height = 600;
  $.get('/data', function(data) {

    var num_words = data.length;

    var scale = d3.scale.linear()
          .domain([0, num_words/2])
          .range([0,height]);
    
    var text = d3.select('#viz').selectAll('text').data(data).enter()
      .append('text')
      .text(function(d) {return d;})
      .attr('x', function(d, i){
        
        var angle = Math.sin(2*(i / num_words)*Math.PI);
        //var offset = 50*Math.sin(2*(i / num_words)*Math.PI);

        if( i > num_words /2 ){
          offset = 50;
          
        }else{
            offset = 0;
          }
        return r*angle + cx;})
    
      .attr('y', function(d, i){

        var pos = i;
        if( i > num_words/2){
          pos = pos - (num_words/2);
        }
        
        return scale(pos);})
          .style('cursor', 'grabbing');

    function dragmove(d) {
      d3.select(this)
        .attr("y", d3.event.y)
        .attr("x", d3.event.x);
    }
    
    var drag = d3.behavior.drag().on('drag', dragmove);
    text.call(drag);
  }
       );
};
