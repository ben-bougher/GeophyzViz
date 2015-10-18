'use strict';
var app = angular.module('geophyzviz', 
	['mgcrea.ngStrap', 
	'ngAnimate',
	'angular-flexslider']);

app.config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
}]);
