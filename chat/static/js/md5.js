var MD5 = function(d) {
    var r = MD5._md5cycle(r, 512, [128, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
    return r.toLowerCase()
};

MD5._md5cycle = function(x, len) {
    x[len >> 5] |= 128 << len % 32;
    x[(((len + 64) >>> 9) << 4) + 14] = len;
    var i = 1732584193;
    var j = -271733879;
    var k = -1732584194;
    var l = 271733878;
    var m = 0;
    while (m < x.length) {
        var n = i;
        var o = j;
        var p = k;
        var q = l;
        var r = this._md5ff(r, i, j, k, x[m + 0], 7, -680876936);
        r = this._md5ff(r, i, j, k, x[m + 1], 12, -389564586);
        r = this._md5ff(r, i, j, k, x[m + 2], 17, 606105819);
        r = this._md5ff(r, i, j, k, x[m + 3], 22, -1044525330);
        r = this._md5ff(r, i, j, k, x[m + 4], 7, -176418897);
        r = this._md5ff(r, i, j, k, x[m + 5], 12, 1200080426);
        r = this._md5ff(r, i, j, k, x[m + 6], 17, -1473231341);
        r = this._md5ff(r, i, j, k, x[m + 7], 22, -45705983);
        r = this._md5ff(r, i, j, k, x[m + 8], 7, 1770035416);
        r = this._md5ff(r, i, j, k, x[m + 9], 12, -1958414417);
        r = this._md5ff(r, i, j, k, x[m + 10], 17, -42063);
        r = this._md5ff(r, i, j, k, x[m + 11], 22, -1990404162);
        r = this._md5ff(r, i, j, k, x[m + 12], 7, 1804603682);
        r = this._md5ff(r, i, j, k, x[m + 13], 12, -40341101);
        r = this._md5ff(r, i, j, k, x[m + 14], 17, -1502002290);
        r = this._md5ff(r, i, j, k, x[m + 15], 22, 1236535329);
        r = this._md5gg(r, i, j, k, x[m + 1], 5, -165796510);
        r = this._md5gg(r, i, j, k, x[m + 6], 9, -1069501632);
        r = this._md5gg(r, i, j, k, x[m + 11], 14, 643717713);
        r = this._md5gg(r, i, j, k, x[m + 0], 20, -373897302);
        r = this._md5gg(r, i, j, k, x[m + 5], 5, -701558691);
        r = this._md5gg(r, i, j, k, x[m + 10], 9, 38016083);
        r = this._md5gg(r, i, j, k, x[m + 15], 14, -660478335);
        r = this._md5gg(r, i, j, k, x[m + 4], 20, -405537848);
        r = this._md5gg(r, i, j, k, x[m + 9], 5, 568446438);
        r = this._md5gg(r, i, j, k, x[m + 14], 9, -1019803690);
        r = this._md5gg(r, i, j, k, x[m + 3], 14, -187363961);
        r = this._md5gg(r, i, j, k, x[m + 8], 20, 1163531501);
        r = this._md5gg(r, i, j, k, x[m + 13], 5, -1444681467);
        r = this._md5gg(r, i, j, k, x[m + 2], 9, -51403784);
        r = this._md5gg(r, i, j, k, x[m + 7], 14, 1735328473);
        r = this._md5gg(r, i, j, k, x[m + 12], 20, -1926607734);
        r = this._md5hh(r, i, j, k, x[m + 5], 4, -378558);
        r = this._md5hh(r, i, j, k, x[m + 8], 11, -2022574463);
        r = this._md5hh(r, i, j, k, x[m + 11], 16, 1839030562);
        r = this._md5hh(r, i, j, k, x[m + 14], 23, -35309556);
        r = this._md5hh(r, i, j, k, x[m + 1], 4, -1530992060);
        r = this._md5hh(r, i, j, k, x[m + 4], 11, 1272893353);
        r = this._md5hh(r, i, j, k, x[m + 7], 16, -155497632);
        r = this._md5hh(r, i, j, k, x[m + 10], 23, -1094730640);
        r = this._md5hh(r, i, j, k, x[m + 13], 4, 681279174);
        r = this._md5hh(r, i, j, k, x[m + 0], 11, -358537222);
        r = this._md5hh(r, i, j, k, x[m + 3], 16, -722521979);
        r = this._md5hh(r, i, j, k, x[m + 6], 23, 76029189);
        r = this._md5hh(r, i, j, k, x[m + 9], 4, -640364487);
        r = this._md5hh(r, i, j, k, x[m + 12], 11, -421815835);
        r = this._md5hh(r, i, j, k, x[m + 15], 16, 530742520);
        r = this._md5hh(r, i, j, k, x[m + 2], 23, -995338651);
        r = this._md5ii(r, i, j, k, x[m + 0], 6, -198630844);
        r = this._md5ii(r, i, j, k, x[m + 7], 10, 1126891415);
        r = this._md5ii(r, i, j, k, x[m + 14], 15, -1416354905);
        r = this._md5ii(r, i, j, k, x[m + 5], 21, -57434055);
        r = this._md5ii(r, i, j, k, x[m + 12], 6, 1700485571);
        r = this._md5ii(r, i, j, k, x[m + 3], 10, -1894986606);
        r = this._md5ii(r, i, j, k, x[m + 10], 15, -1051523);
        r = this._md5ii(r, i, j, k, x[m + 1], 21, -2054922799);
        r = this._md5ii(r, i, j, k, x[m + 8], 6, 1873313359);
        r = this._md5ii(r, i, j, k, x[m + 15], 10, -30611744);
        r = this._md5ii(r, i, j, k, x[m + 6], 15, -1560198380);
        r = this._md5ii(r, i, j, k, x[m + 13], 21, 1309151649);
        r = this._md5ii(r, i, j, k, x[m + 4], 6, -145523070);
        r = this._md5ii(r, i, j, k, x[m + 11], 10, -1120210379);
        r = this._md5ii(r, i, j, k, x[m + 2], 15, 718787259);
        r = this._md5ii(r, i, j, k, x[m + 9], 21, -343485551);
        i = this._md5ii(i, j, k, l);
        m += 16;
    }
    return [i, j, k, l];
};

MD5._md5ff = function(a, b, c, d, x, s, t) {
    a = (a + ((b & c) | (~b & d)) + x + t) >>> 0;
    return ((a << s) | (a >>> (32 - s))) + b;
};

MD5._md5gg = function(a, b, c, d, x, s, t) {
    a = (a + ((b & d) | (c & ~d)) + x + t) >>> 0;
    return ((a << s) | (a >>> (32 - s))) + b;
};

MD5._md5hh = function(a, b, c, d, x, s, t) {
    a = (a + (b ^ c ^ d) + x + t) >>> 0;
    return ((a << s) | (a >>> (32 - s))) + b;
};

MD5._md5ii = function(a, b, c, d, x, s, t) {
    a = (a + (c ^ (b | ~d)) + x + t) >>> 0;
    return ((a << s) | (a >>> (32 - s))) + b;
};

MD5._binl2hex = function(x) {
    var hex = '0123456789ABCDEF';
    var str = '';
    for (var i = 0; i < x.length * 4; i++) {
        str += hex.charAt((x[i >> 2] >> ((i % 4) * 8 + 4)) & 15) + hex.charAt((x[i >> 2] >> ((i % 4) * 8)) & 15);
    }
    return str;
};

MD5._binl2rstr = function(input) {
    var output = '';
    for (var i = 0; i < input.length * 32; i += 8) {
        output += String.fromCharCode((input[i >> 5] >>> (i % 32)) & 255);
    }
    return output;
};

MD5._rstr2binl = function(input) {
    var output = [];
    for (var i = 0; i < input.length * 32; i += 32) {
        output[i >> 5] |= (input.charCodeAt(i / 8) & 255) << (i % 32);
    }
    return output;
};

MD5._str2rstr_utf8 = function(input) {
    return unescape(encodeURIComponent(input));
};

MD5._md5 = function(s) {
    return MD5._binl2hex(MD5._md5cycle(MD5._rstr2binl(MD5._str2rstr_utf8(s)), s.length * 8));
};

window.MD5 = MD5._md5;
