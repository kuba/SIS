unused_numbers = function(){
    // Return unused numbers.
    var numbers = $('#unused_numbers>li');
    return $.map(numbers, function(e, i){
        return e.innerText;
    });
};

number_inputs = function(){
    // Return lucky numbers input fields.
    return $("input[name^='lucky-'][name$='number']");
};

date_inputs = function(){
    // Return date input fields.
    return $("input[id^='lucky-'][id$='-date']");
};

shuffle = function(v){
    // Shuffle an array.
    for(var j, x, i = v.length; i; j = parseInt(Math.random() * i), x = v[--i], v[i] = v[j], v[j] = x);
    return v;
};

draw = function(){
    // Shuffle lucky numbers and set appropriate input values.
    var shuffled = shuffle(unused_numbers());
    number_inputs().each(function(index, element){
        if (shuffled[index])
            element.value = shuffled[index];
    });
};

clear_numbers = function(){
    // Clear lucky numbers input fields.
    number_inputs().each(function(index, element){
        element.value = "";
    });
};

$(document).ready(function() {
    // Add the link for drawing and clearing
    $('form').prepend(
        '<a id="draw" href="#">Losuj!</a> ',
        '<a id="clear" href="#">Wyczyść numerki!</a><br />');
    $('a#draw').click(draw);
    $('a#clear').click(clear_numbers);

    // Add jQuery date picker to appropriate input fields.
    date_inputs().each(function (index, element){
            $(element).datepicker({"dateFormat":"dd/mm/yy"});
    });

});
