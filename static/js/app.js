'use strict';
var app = angular.module('geophyzviz', 
	['mgcrea.ngStrap', 
	'ngAnimate',
	'angular-flexslider']);

app.config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
}]);



app.controller('2DCtrl', function ($scope, $http, $alert, $timeout) {
  var a = 1;
});

// <-- HELPER FUNCTIONS --> //
// Take two numbers and return the abs max of the two
function getMax(a, b){
  if(Math.abs(a) > Math.abs(b)){
    return Math.abs(a);
  } else {
    return Math.abs(b);
  }
}



// Get a row from a columnar matrix
function getCrossSection(matrix, value, sampleRate){
    var arr = [];
    var rowIndex = Math.floor(value / sampleRate);
  for(var i = 0; i < matrix.length; i++){
    arr.push(matrix[i][rowIndex]);
  }
  return arr;

}
