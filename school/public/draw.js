shuffle = function(v){
    // Shuffle array
    for(var j, x, i = v.length; i; j = parseInt(Math.random() * i), x = v[--i], v[i] = v[j], v[j] = x);
    return v;
};

draw = function(){
    // Shuffle and set input values
    var shuffled = shuffle(numbers);
    inputs.each(function(index, element){
        if (shuffled[index])
            element.value = shuffled[index];
    });
};

clear = function(){
    inputs.each(function(index, element){
        element.value = "";
    });
};

$(document).ready(function() {

    // Get the numbers that can be drawed
    //numbers = $('#not_used_numbers>li');
    //numbers = $.map(numbers, function(e, i){
    //    return e.innerText
    //});

    // Form inputs
    inputs = $("input[id^='lucky'][id$='number']");

    // Add the link for drawing
    $('form').prepend(
        '<a id="draw" href="#">Draw!</a> ',
        '<a id="clear" href="#">Clear!</a><br />');
    $('a#draw').click(draw);
    $('a#clear').click(clear);

});
