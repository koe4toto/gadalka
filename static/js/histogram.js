var twoColComp = {
  init: function (){
    var tables = document.getElementsByTagName('table');

    for(var i = 0; i < tables.length; i++) {
      if (new RegExp('(^| )two-column-comp( |$)', 'gi').test(tables[i].className)){
         return;
      }

      var h = tables[i].clientHeight,
          t = tables[i].getBoundingClientRect().top,
          wT = window.pageYOffset || document.documentElement.scrollTop,
          wH = window.innerHeight;

      if(wT + wH > t + h/2){
         this.make(tables[i]);
       }
    }
  },

  make : function(el){

    var rows = el.getElementsByTagName('tr'),
        vals = [],
        max,
        percent;

    for(var x = 0; x < rows.length; x++) {
      var cells = rows[x].getElementsByClassName('numb');
      for(var y = 0; y < cells.length; y++){
        vals.push(parseInt(cells[y].innerHTML, 10));
      }
    }

    max = Math.max.apply( Math, vals );
    percent = 100/max;

    const columnsCount = cells.length;
    let maxValues = [];
    let percentValues = [];

    for(var x = 0; x < rows.length; x++) {
      maxValues.push([]);
      percentValues.push([]);
    }

    for(let count = 0; count < columnsCount; count++) {
      maxValues[count] = Math.max.apply( Math, vals.filter((value, index) => index%columnsCount === count));
      percentValues[count] = 100/maxValues[count];  // 100/Math.max.apply( Math, vals.filter((value, index) => index%columnsCount === count));

    }

    for(x = 0; x < rows.length; x++) {
      var cells = rows[x].getElementsByClassName('numb');
      for(var y = 0; y < cells.length; y++){
        var currNum = parseInt(cells[y].innerHTML, 10);
        cells[y].style.backgroundSize = percentValues[(y) % columnsCount] * currNum - 10 + "% 100%";
        cells[y].style.transitionDelay = x/20 + "s";
      }
    }

    el.className =+ " two-column-comp"
  }
}

window.onload = function(){
  twoColComp.init();
}

window.onscroll = function(){
  twoColComp.init();
}
