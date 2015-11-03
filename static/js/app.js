'use strict';
var app = angular.module('viz', 
	['mgcrea.ngStrap', 
	'ngAnimate',
	'angular-flexslider']);

app.config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
}]);


app.controller('controller', function($scope, $http) {

  $scope.setDefaults = function(){

    $scope.r = 200;
    $scope.cy = 300;
    $scope.cx = 300;
    
    // Init the canvas
    $scope.svg = d3.select("#viz");
    $scope.height = 500;
    
    // Define define the trashbin location
    $scope.trash_x1 = 0;
    $scope.trash_x2 = 40;
    $scope.trash_y1 = 0;
    $scope.trash_y2 = 40;

    // Bring in the data
    $http.get('/data').then(function(response) {

      var data = response.data;
      $scope.keywords = data.keys;
      $scope.suggestions = data.suggestions;

      $scope.initCloud();
      
      // Do the other paper titles
      var pap_div = d3.select("#papers");

      pap_div.selectAll('p').data($scope.suggestions).enter().append('p')
        .text(function(d){
          return d.title;})
        .style('cursor', 'pointer')
        .on('click', function(d) { window.open(d.doi); });
      
    });
    
  };
  
  $scope.initCloud = function(){
    
    var num_words = $scope.keywords.length;
    $scope.scale = d3.scale.linear()
      .domain([0, num_words/2])
      .range([50, $scope.height-50]);

    var text = d3.select('#viz').selectAll('text')
          .data($scope.keywords).enter()
          .append('text')
          .text(function(d) {return d;})
          .attr('class','normaltext')
          .attr('x', function(d, i){
        
            var angle = Math.sin(2*(i / num_words)*Math.PI);
            //var offset = 50*Math.sin(2*(i / num_words)*Math.PI);

            var offset = 0;
            if( i > num_words /2 ){
              offset = 50;
              
            }
            
            return $scope.r*angle + $scope.cx;})
    
          .attr('y', function(d, i){

            var pos = i;
            if( i > num_words/2){
              pos = pos - (num_words/2);
            }
        
            return $scope.scale(pos) + 10;})
          .style('cursor', 'grabbing');

    var dragend = function dragend(d,i){

      var item = d3.select(this);
      if((item.attr('x') < $scope.trash_y2) &&
         (item.attr('y') < $scope.trash_x2)){
        
        item.remove();
        $scope.keywords.splice(i,1);
        
      }
      
      $scope.updateSuggestions();
    };

    var dragmove = function dragmove(d, i) {
      
      var word = d3.select(this)
            .attr("y", d3.event.y)
            .attr("x", d3.event.x);

      $scope.keywords[i].dist = ($scope.cx - d3.event.x) *
        ($scope.cy - d3.event.y);
      
      
      if((d3.event.y < $scope.trash_y2) &&
         (d3.event.x < $scope.trash_x2)){
      
        word.style('fill', 'red');
      }
      else{
        word.style('fill', 'black');
      }
    };

    var drag = d3.behavior.drag().on('drag', dragmove)
          .on('dragend', dragend);

    text.call(drag);
  };

  $scope.updateSuggestions = function updateSuggestions(){

    var data = JSON.stringify({data: $scope.keywords});
    $http.get('/suggest?' + data).then(function(response){
      var data = response.data;

      $scope.suggestions = data;
      var pap_div = d3.select("#papers");

      pap_div.selectAll('p').data($scope.suggestions)
        .text(function(d){return d.title;})
    });
  };
                                       
  $scope.setDefaults();

});
