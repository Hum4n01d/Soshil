'use strict';

var gulp = require('gulp'),
    stylus = require('gulp-stylus');

gulp.task('compileStylus', function() {
  return gulp.src('static/**.styl')
    .pipe(stylus({
      compress: true
    }))
    .pipe(gulp.dest('static/'));
});

gulp.task('watchStylus', function() {
  gulp.watch('static/**.styl', ['compileStylus']);
});

gulp.task('default', ['compileStylus', 'watchStylus']);