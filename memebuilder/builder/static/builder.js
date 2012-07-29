function constrainSize(changed) {
    h = document.getElementById('height');
    w = document.getElementById('width');
    if ('height' == changed) {
        w.value = h.value * w.defaultValue / h.defaultValue;
        
    } else {
        h.value = w.value * h.defaultValue / w.defaultValue;
    }
}
