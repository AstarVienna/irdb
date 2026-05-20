/**
* General JavaScript Functions
* 08.04.2008 gzech created
*
**/

/* Obfuscate Email Address */

function createM (name, domain, text) {
	var mailadd = name+'&#64;'+domain;
	var url = "mailto:" + mailadd;
	if (!text) {
	text = mailadd;
	}
	document.write("<a href=\"" + url + "\">" + text + "</a>");
}

function createEsoM (name, text) {
	var mailadd = name+'&#64;eso.org';
	var url = "mailto:" + mailadd;
	if (!text) {
	text = mailadd;
	}
	document.write("<a href=\"" + url + "\">" + text + "</a>");

}

function homeTeaserSwitch (elname, text, highlight) {

    document.getElementById(elname).firstChild.nodeValue = text;
/* not needed at the moment
    document.getElementById(highlight).className = 'left pr_highlight';
    var i = highlight;
    if (i==0 || i==1)  document.getElementById(2).className = 'left';
    if (i==0 || i==2)  document.getElementById(1).className = 'left';
    if (i==2 || i==1)  document.getElementById(0).className = 'left';
*/
}

function homeTeaserClear (elname) {
//    document.getElementById(elname).className = 'left';
}

function clearField(elname,defval) {
	var curval = document.getElementById(elname).value;
	if (curval == defval) {
		document.getElementById(elname).value='';
	}
}

function setField (elname, defval) {
	var curval = document.getElementById(elname).value;
	if (curval == "") {
		document.getElementById(elname).value=defval;
	}
}