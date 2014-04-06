booklist = new Array;
displaybooklist = new Array;
sortby = "";
booklabel = "";
booklabels = new Array;
searchterms = "";
reverse = true;
useand = true;
batchedit = false;
viewarchived = false;

function SetDefaults(preferredsort, ascending) {
  sortby = preferredsort;
  booklabel = "";
  searchterms = "";
  if (ascending == "True") { reverse = false } else { reverse = true }
}

function Overlay(url) {

   var overlay = document.createElement("div");
   overlay.setAttribute("id","overlay");
   overlay.setAttribute("class", "overlay");
   document.body.appendChild(overlay);
   
   var overlayform = document.createElement("div");
   overlayform.setAttribute("id","overlayform");
   overlayform.setAttribute("class", "overlayform");
   document.body.appendChild(overlayform);

   if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
     var xmlhttp=new XMLHttpRequest();
   }
   else {// code for IE6, IE5
     var xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
   }
  
   xmlhttp.open("GET", url, true);
   xmlhttp.send();
   
   xmlhttp.onreadystatechange=function() {
     if (xmlhttp.readyState==4 && xmlhttp.status==200) {
       overlayform.innerHTML = xmlhttp.responseText;
      }
    }
       overlayform.innerHTML = "Loading...";
}

function ClearOverlay() {
   var overlay = document.getElementById("overlay");
   document.body.removeChild(overlay);

   var overlayform = document.getElementById("overlayform");
   document.body.removeChild(overlayform);
}

function GetAndStrip(url) {
  var xmlhttp;

  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.open("GET", url, true);
  xmlhttp.send();
  fullhtml = xmlhttp.responseText;
  
  return fullhtml;
  
}

function AddLabel() {
  var labelsdiv = document.getElementById("labelsdiv");
  var div = document.createElement("div");
  var numlabelsinput = document.getElementById("numlabels");
  var numlabels = parseInt(numlabelsinput.value);
  div.setAttribute("name", "labeldiv");
  labelsdiv.appendChild(div);
  
  var label = document.createElement("input");
  label.setAttribute("type", "text");
  label.setAttribute("name", "label" + numlabels);
  label.setAttribute("id", numlabels);
  div.appendChild(label);
  
  numlabelsinput.setAttribute("value", numlabels+1);
  
  if (numlabels > 19) {
    var addlabel = document.getElementById("addlabel");
    addlabel.setAttribute("class", "invisible");
  }

}

function CollapseMenu(menuid, toggleid) {
  var menu = document.getElementById(menuid);
  var toggle = document.getElementById(toggleid);
  var currentclass = menu.getAttribute("class")
  if (currentclass == "hiddensidebar") {
    menu.setAttribute("class","sidebar");
    toggle.innerHTML = "[-]";
  }
  else {
    menu.setAttribute("class","hiddensidebar");
    toggle.innerHTML = "[+]";
  }
}

function ToggleLabel(label) {
  var labelelement = document.getElementById(label + "toggle")
  var currentclass = labelelement.getAttribute("class")
  if (currentclass == "link") {
    labelelement.setAttribute("class","boldlink");
    booklabels.push(label);
  }
  else {
    labelelement.setAttribute("class","link");
    for (booklabel in booklabels) {
      if (label == booklabels[booklabel]) {
        booklabels.splice(booklabel, 1);
      }
    }
  }
  FillDisplayBooks();
  FillMyBooksTable();
}

function ToggleArchive() {
  var mybooks = document.getElementById("mybooks");
  var archive = document.getElementById("archive");
  var currentclass = mybooks.getAttribute("class");
  if (currentclass == "activetab") {
    mybooks.setAttribute("class","tab");
    archive.setAttribute("class","activetab");
    viewarchived = true;
  }
  else {
    archive.setAttribute("class","tab");
    mybooks.setAttribute("class","activetab");
    viewarchived = false;
  }
  FillDisplayBooks();
  FillMyBooksTable();
}

function ChangeAndOr() {
  var andtoggle = document.getElementById("and");
  useand = andtoggle.checked;
  FillDisplayBooks();
  FillMyBooksTable();
}

function ChangeBatch() {
  var batchtoggle = document.getElementById("batchon");
  batchedit = batchtoggle.checked;
  FillMyBooksTable();
}

function BatchCheckAll() {
  var checkboxes = document.getElementsByName("batcheditcheck");
  var mastercheck = document.getElementById("batchcheckall");
  for (checkbox in checkboxes) {
    checkboxes[checkbox].checked = mastercheck.checked;
  }
}

// ------------- Sorting and Searching ------------------

function SearchMyBooks() {
  searchterms = document.getElementById("query").value;
  searchvaluespan = document.getElementById("searchvalue");
  clearsearchspan = document.getElementById("clearsearch");
  searchvaluespan.setAttribute('class', 'searchvisible');
  clearsearchspan.setAttribute('class', 'clearsearch');
  searchvaluespan.innerHTML = searchterms;
  FillDisplayBooks();
  FillMyBooksTable();
  return false;
}

function ClearSearchTerms() {
  searchterms = "";
  searchvaluespan = document.getElementById("searchvalue");
  clearsearchspan = document.getElementById("clearsearch");
  searchvaluespan.setAttribute('class', 'invisible');
  clearsearchspan.setAttribute('class', 'invisible');
  searchvaluespan.innerHTML = "";
  FillDisplayBooks();
  FillMyBooksTable();
  return false;
}

function SortDisplayBooks() {
  switch (sortby) {
    case "price": displaybooklist.sort(comparePrices);
      break;
    case "date": displaybooklist.sort(compareDates);
      break;
    case "title": displaybooklist.sort(compareTitles);
      break;
    case "author": displaybooklist.sort(compareAuthors);
      break;
    default: displaybooklist.sort(compareDates);
  }
  if (reverse) displaybooklist.reverse();
}

function ChangeSort() {
  var selectbox = document.getElementById("sortorder");
  sortby = selectbox.options[selectbox.selectedIndex].value;
  SortDisplayBooks();
  FillMyBooksTable();
}

function ChangeAscDesc() {
  var descending = document.getElementById("descending");
  reverse = descending.checked;
  SortDisplayBooks();
  FillMyBooksTable();
}

// ---------------- compares -------------------------

function compareAuthors(a,b) {
  var alast = a.author.split(" ").pop();
  var blast = b.author.split(" ").pop();
  if (alast < blast) return -1;
  if (alast > blast) return 1;
  return compareTitles(a,b);
}

function compareDates(a,b) {
  if (a.dateadded < b.dateadded) return -1;
  if (a.dateadded > b.dateadded) return 1;
  return 0;
}

function comparePrices(a,b) {
  if (a.price.length < b.price.length) return -1;
  if (a.price.length > b.price.length) return 1;
  if (a.price < b.price) return -1;
  if (a.price > b.price) return 1;
  return compareAuthors(a,b);
}

function compareTitles(a,b) {
  var atitle = a.title.toLowerCase().split(" ");
  var btitle = b.title.toLowerCase().split(" ");
  if (atitle[0] == "the" || atitle[0] == "an" || atitle[0] == "a") atitle.shift();
  if (btitle[0] == "the" || btitle[0] == "an" || btitle[0] == "a") btitle.shift();
  if (atitle < btitle) return -1;
  if (atitle > btitle) return 1;
  return 0
}

// ---------------- Get and Display Books -------------------

function LoadBooksXML() {
  var xmlhttp,xmldoc,books,bookinfo,i,j;
  var labels = new Array()
  var formatprice = new Object()
  var formaturl = new Object()
  
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState==4 && xmlhttp.status==200) {
      booklist.length=0;
      books = xmlhttp.responseText;
      books = xmlhttp.responseXML.documentElement.getElementsByTagName("DisplayBook");
      bookinfo = "";
      for (i=0;i<books.length;i++) {
        try {
          book = new Object();
          book.author = books[i].getElementsByTagName('author')[0].firstChild.nodeValue;
          book.title = books[i].getElementsByTagName('title')[0].firstChild.nodeValue;
          book.price = books[i].getElementsByTagName('price')[0].firstChild.nodeValue;
          book.dateadded = books[i].getElementsByTagName('dateadded')[0].firstChild.nodeValue;
          book.goodreadsid = books[i].getElementsByTagName('goodreadsid')[0].firstChild.nodeValue;
          try {
            book.small_img_url = books[i].getElementsByTagName('small_img_url')[0].firstChild.nodeValue;
          } catch (er) {
            book.small_img_url = "broken"
          }
          book.priceavailable = books[i].getElementsByTagName('priceavailable')[0].firstChild.nodeValue;
          book.free = books[i].getElementsByTagName('free')[0].firstChild.nodeValue;
          book.labels = [];
          var labels = books[i].getElementsByTagName('label');
          for (j=0;j<labels.length;j++) {
            book.labels.push(labels[j].firstChild.nodeValue);
          }
          book.formatprice = {};
          var formatprices = books[i].getElementsByTagName('formatprices')[0].childNodes;
          for (j=0; j<formatprices.length;j++) {
            var format = formatprices[j].nodeName;
            book.formatprice[format] = formatprices[j].textContent;
          }
          book.formaturl = {}
          var formaturls = books[i].getElementsByTagName('formaturls')[0].childNodes;
          for (j=0; j<formaturls.length;j++) {
            var format = formaturls[j].nodeName;
            book.formaturl[format] = formaturls[j].textContent;
          }
          
          booklist.push(book);
          
        } 
        catch (er) { }
      }
      
      FillDisplayBooks();
      FillMyBooksTable();
    }
  }

  xmlhttp.open("GET","/getdisplaybooks.xml",true);
  xmlhttp.send();
}

function FillDisplayBooks() {
  displaybooklist.length = 0;
  for (book in booklist) {
    var labeledarchived = false;
    var haslabel = false
    var hassearch = true
    for (label in booklist[book].labels) {
      if (booklist[book].labels[label] == "archived") {
        labeledarchived = true;
        break;
      }
    }
    if (labeledarchived != viewarchived) {
      haslabel = false;
    } 
    else if (booklabels.length == 0) {
      haslabel = true;
    }
    else {
      if (useand) {
        for (activelabel in booklabels) {
		  for (label in booklist[book].labels) {
		    haslabel = false;
			if (booklabels[activelabel] == booklist[book].labels[label]) {
			  haslabel = true;
			  break;
			}
		  }
		  if (haslabel == false) {
		    break;
		  }
		}
      }
      else {
        for (activelabel in booklabels) {
		  for (label in booklist[book].labels) {
			if (booklabels[activelabel] == booklist[book].labels[label]) {
			  haslabel = true;
			}
		  }
		}
      }
    }
    if (searchterms != "") {
      searchwords = searchterms.split(" ");
      for (var word in searchwords) {
        if (!(booklist[book].author.toLowerCase().match(searchwords[word].toLowerCase()) || booklist[book].title.toLowerCase().match(searchwords[word].toLowerCase()))) {
          hassearch = false;
        }
      }
    }
    if (haslabel && hassearch) displaybooklist.push(booklist[book]);
  }
  SortDisplayBooks();
}

function FillMyBooksTable() {
      var table = document.getElementById("booklist");
      var status = document.getElementById("status");
      var coverheader = document.getElementById("coverheader");
      status.setAttribute("class", "invisible");

      if (batchedit){
        coverheader.innerHTML = "<input type='checkbox' name='batchcheckall' id='batchcheckall' onclick='BatchCheckAll()'>";
      }
      else {
        coverheader.innerHTML = "Cover";
      }

      
      for (var i = table.rows.length-1; i>0; i--) {
        table.deleteRow(i);
      }
      for (book in displaybooklist) {
          var actioninfo = "";
          var formatinfo = "";
          var labelinfo = "";
          var row = table.insertRow(-1);
          var imagecell = row.insertCell(0);
          var titleauthorcell = row.insertCell(1);
          var pricecell = row.insertCell(2);
          var formatcell = row.insertCell(3);
          var labelcell = row.insertCell(4);
          var actioncell = row.insertCell(5);
          
          if (displaybooklist[book].free == "True") {
            row.setAttribute("class", "pricefree");
          }
          else if (displaybooklist[book].priceavailable == "True") {
            row.setAttribute("class", "priceavailable");
          }
          else if (book % 2 == 0) {
            row.setAttribute("class", "odd");
          }
          else {
            row.setAttribute("class", "even");
          }

          
          if (batchedit){
            imagecell.innerHTML = "<input type='checkbox' name='batcheditcheck' id='batch" + displaybooklist[book].goodreadsid + "'>";
          }
          else {
            imagecell.innerHTML = "<img src=\"" + displaybooklist[book].small_img_url + "\">";
          }
          titleauthorcell.innerHTML = "<a href = \"http://www.goodreads.com/work/editions/" + displaybooklist[book].goodreadsid + "\">" + displaybooklist[book].title + "</a><br>" + displaybooklist[book].author;
          pricecell.innerHTML = displaybooklist[book].price;
          for (var format in displaybooklist[book].formatprice){
            formatinfo = formatinfo + format
            if (displaybooklist[book].formatprice[format] != "") {
              formatinfo = formatinfo + " (<a href = " + displaybooklist[book].formaturl[format] + ">" + displaybooklist[book].formatprice[format] + "</a>)";
            }
            formatinfo = formatinfo + "<br>";
          }
          formatcell.innerHTML = formatinfo;
          for (var label in displaybooklist[book].labels){
            labelinfo = labelinfo + displaybooklist[book].labels[label] + "<br>";
          }
          labelcell.innerHTML = labelinfo;
          if (viewarchived){
            actioninfo = actioninfo + "<span class='link'  onclick='RestoreBook(" + displaybooklist[book].goodreadsid + ")' >restore</span><br>";
            actioninfo = actioninfo + "<span class='link'  onclick='DeleteBook(" + displaybooklist[book].goodreadsid + ")' >delete</span><br>";
          }
          else {
            actioninfo = actioninfo + "<span class='link'  onclick='Overlay(\"/edit?bookid=" + displaybooklist[book].goodreadsid + "\")' >edit</span><br>";
            actioninfo = actioninfo + "<span class='link'  onclick='ArchiveBook(" + displaybooklist[book].goodreadsid + ")' >archive</span><br>";
          }
          actioncell.innerHTML = actioninfo;

      }
}

// ----------------- Form Checking -------------------

function AccountSettingsSubmit() {
    var validprice = document.getElementById("validprice");
    var validemail = document.getElementById("validemail");
    var validwait = document.getElementById("validwait");
    
    var price = document.getElementById("defaultprice");
    var email = document.getElementById("preferredemail");
    var wait = document.getElementById("wait");

    var returnvalue = true;
    var wholeexp = new RegExp("^[0-9]+$");
    var centexp = new RegExp("^[0-9]*\.[0-9][0-9]$");
    var emailexp = new RegExp("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$");
    
    if (wholeexp.test(price.value) || centexp.test(price.value) || price.value=="") {
      validprice.setAttribute("class", "valid");
    } else {
      validprice.setAttribute("class", "invalid");
      returnvalue = false;
    }
    
    if (wholeexp.test(wait.value) ) {
      validwait.setAttribute("class", "valid");
    } else {
      validwait.setAttribute("class", "invalid");
      returnvalue = false;
    }
    
    if (emailexp.test(email.value)) {
      validemail.setAttribute("class", "valid");
    } else {
      validemail.setAttribute("class", "invalid");
      returnvalue = false;
    }
    
    return returnvalue;
}

function BookAddSubmit() {
    var validprice = document.getElementById("validprice");
    var validbook = document.getElementById("validbook");
    var validformat = document.getElementById("validformat");
    var price = document.getElementById("price");
    var returnvalue = true;
    var bookids = document.getElementsByName("bookid");
    var noneselected = true;
    var wholeexp = new RegExp("^[0-9]+$");
    var centexp = new RegExp("^[0-9]*\.[0-9][0-9]$");
    
    if (wholeexp.test(price.value) || centexp.test(price.value)) {
      validprice.setAttribute("class", "valid");
    } else {
      validprice.setAttribute("class", "invalid");
      returnvalue = false;
    }
        
    for (var i=0; i<bookids.length; i++) {
      if (bookids[i].checked) {
        noneselected = false;
      } 
    }
    
    if (noneselected) {
      returnvalue = false;
      validbook.setAttribute("class", "invalid");
    } else {
	  validbook.setAttribute("class", "valid");
    }

    var formats = document.getElementsByName("format");
    noneselected = true;
    
    for (var i=0; i<formats.length; i++) {
      if (formats[i].checked) {
        noneselected = false;
      }
    }
    
    if (noneselected) {
      returnvalue = false;
      validformat.setAttribute("class", "invalid");
    } else {
      validformat.setAttribute("class", "valid");
    }
    
    return returnvalue;
}

function BookEditSubmit() {
    var validprice = document.getElementById("validprice");
    var validbook = document.getElementById("validbook");
    var validformat = document.getElementById("validformat");
    var price = document.getElementById("price");
    var returnvalue = true;
    var noneselected = true;
    var wholeexp = new RegExp("^[0-9]+$");
    var centexp = new RegExp("^[0-9]*\.[0-9][0-9]$");
    
    if (wholeexp.test(price.value) || centexp.test(price.value)) {
      validprice.setAttribute("class", "valid");
    }
    else {
      validprice.setAttribute("class", "invalid");
      returnvalue = false;
    }
        
    var formats = document.getElementsByName("format");
    noneselected = true;
    
    for (var i=0; i<formats.length; i++) {
      if (formats[i].checked) {
        noneselected = false;
      }
    }
    
    if (noneselected) {
      returnvalue = false;
      validformat.setAttribute("class", "invalid");
    }
    else {
      validformat.setAttribute("class", "valid");
    }
    
    return returnvalue;
}

// ------------------ Book Editing -----------------------

function ArchiveBook(goodreadsid) {
  var xmlhttp, url;
  url = "/archive?bookid=" + goodreadsid;
  var status = document.getElementById("status");
  status.setAttribute("class", "invisible");
  
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.open("GET", url, true);
  xmlhttp.send();
  
  xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState==4 && xmlhttp.status==200) {
      status.innerHTML = "Book Archived";
      status.setAttribute("class", "status");
    }
  }
  
  for (var book in booklist) {
    if (booklist[book].goodreadsid == goodreadsid) {
      booklist[book].labels.push('archived');
    }
  }
  
  FillDisplayBooks();
  FillMyBooksTable();
  
}

function DeleteBook(goodreadsid) {
  var xmlhttp, url;
  url = "/delete?bookid=" + goodreadsid;
  var status = document.getElementById("status");
  status.setAttribute("class", "invisible");

  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.open("GET", url, true);
  xmlhttp.send();
  
  xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState==4 && xmlhttp.status==200) {
      status.innerHTML = "Book Deleted";
      status.setAttribute("class", "status");
    }
  }
  
  for (var book in booklist) {
    if (booklist[book].goodreadsid == goodreadsid) {
      booklist.splice(book, 1);
    }
  }
  
  FillDisplayBooks();
  FillMyBooksTable();
  
}

function RestoreBook(goodreadsid) {
  var xmlhttp, url, tags;
  url = "/restore?bookid=" + goodreadsid;
  var status = document.getElementById("status");
  status.setAttribute("class", "invisible");

  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.open("GET", url, true);
  xmlhttp.send();
  
  xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState==4 && xmlhttp.status==200) {
      status.innerHTML = "Book Restored";
      status.setAttribute("class", "status");
    }
  }
  
  for (var book in booklist) {
    if (booklist[book].goodreadsid == goodreadsid)  {
      try {
        var archivedindex = booklist[book].labels.indexOf('archived');
        booklist[book].labels.splice(archivedindex, 1);
      }
      catch(e){
      }
    }
  }
  
  FillDisplayBooks();
  FillMyBooksTable();
  
}

function EditBook(goodreadsid) {
  var xmlhttp, url;
  var labelvalues = [], formatvalues = [], pricedict={}, urldict={};
  var status = document.getElementById("status");
  status.setAttribute("class", "invisible");

  var price = document.getElementById("price").value;
  var formats = document.getElementsByName("format");
  var labels = document.getElementsByName("label");
  
  var post = "bookid=" + goodreadsid + "&price=" + price;
    
  for (var i=0; i<formats.length; i++) {
    if (formats[i].checked) {
      post = post + "&format=" + formats[i].value;
      formatvalues.push(formats[i].value);
    }
  }

  for (var i=0; i<labels.length; i++) {
    if (labels[i].checked) {
      post = post + "&label=" + labels[i].value;
      labelvalues.push(labels[i].value);
    }
  }

  url = "/add?" + post;
    
  
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.open("GET", url, true);
  xmlhttp.send();
  
  for (var book in booklist) {
    if (booklist[book].goodreadsid == goodreadsid) {
      for (var i in formatvalues) {
        try {
          if (booklist[book].formatprice[formatvalues[i]]) {
            pricedict[formatvalues[i]] = booklist[book].formatprice[formatvalues[i]];
            urldict[formatvalues[i]] = booklist[book].formaturl[formatvalues[i]];
          }
          else {
            pricedict[formatvalues[i]] = "";
            urldict[formatvalues[i]] = "";
          }
        }
        catch (er) {
          pricedict[formatvalues[i]] = "";
        }
      }
      booklist[book].formatprice = pricedict;
      booklist[book].formaturl = urldict;
      booklist[book].price = price;
      booklist[book].labels = labelvalues;
    }
  }
  
  ClearOverlay();
  FillDisplayBooks();
  FillMyBooksTable();
  
}

function ChangeSelected(method) {
  var checkboxes = document.getElementsByName('batcheditcheck');
  var selectedids = [];
  var post;
  for (var box in checkboxes) {
    if (checkboxes[box].checked) {
      var id = checkboxes[box].id;
      try{
        selectedids.push(id.slice(5));
      }
      catch(e){
      }
    }
  }
  
  switch(method) {
    case "addlabel":
      var labelselect = document.getElementById('batchlabels');
      var label = labelselect.options[labelselect.selectedIndex].text;
      for (var goodreadsid in selectedids) {
        for (var book in booklist) {
          if (booklist[book].goodreadsid == selectedids[goodreadsid]) {
            var exists = false;
            for (var i in booklist[book].labels) {
              if (booklist[book].labels[i] == label) {
                exists = true;
                break;
              }
            }
            if (exists == false) {
              booklist[book].labels.push(label)
            }
            break;
          }
        }
      }
      post = "";
      for (goodreadsid in selectedids) {
        post = post + "bookid=" + selectedids[goodreadsid] + "&";
      }
      post = post + "label=" + label + "&action=" + method;
      break;
    case "removelabel":
      var labelselect = document.getElementById('batchlabels');
      var label = labelselect.options[labelselect.selectedIndex].text;
      for (var goodreadsid in selectedids) {
        for (var book in booklist) {
          if (booklist[book].goodreadsid == selectedids[goodreadsid]) {
			  try {
				var labelindex = booklist[book].labels.indexOf(label);
				booklist[book].labels.splice(labelindex, 1);
			  }
			  catch(e){
			  }
            break;
          }
        }
      }
      post = "";
      for (goodreadsid in selectedids) {
        post = post + "bookid=" + selectedids[goodreadsid] + "&";
      }
      post = post + "label=" + label + "&action=" + method;
      break;
    case "addformat":
      var formatselect = document.getElementById('batchformats');
      var format = formatselect.options[formatselect.selectedIndex].text;
      for (var goodreadsid in selectedids) {
        for (var book in booklist) {
          if (booklist[book].goodreadsid == selectedids[goodreadsid]) {
            try {
              if (booklist[book].formatprice[format]) {
                dummy = "5";
              }
              else {
                booklist[book].formatprice[format] = "";
                booklist[book].formaturl[format] = "";
              }
            }
            catch(e) {
              booklist[book].formatprice[format] = "";
              booklist[book].formaturl[format] = "";
            }
            break;
          }
        }
      }
      post = "";
      for (goodreadsid in selectedids) {
        post = post + "bookid=" + selectedids[goodreadsid] + "&";
      }
      post = post + "format=" + format + "&action=" + method;
      break;
    case "removeformat":
      var formatselect = document.getElementById('batchformats');
      var format = formatselect.options[formatselect.selectedIndex].text;
      for (var goodreadsid in selectedids) {
        for (var book in booklist) {
          if (booklist[book].goodreadsid == selectedids[goodreadsid]) {
            booklist[book].formatprice[format] = "";
            booklist[book].formaturl[format] = "";
            delete booklist[book].formatprice[format];
            delete booklist[book].formaturl[format];
            break;
          }
        }
      }
      post = "";
      for (goodreadsid in selectedids) {
        post = post + "bookid=" + selectedids[goodreadsid] + "&";
      }
      post = post + "format=" + format + "&action=" + method;
      break;
    case "price":
//       var pricebox = document.getElementById('batchprice');
//       var price = pricebox.value;
//       for (var goodreadsid in selectedids) {
//         for (var book in booklist) {
//           booklist[book].goodreadsid = price;
//         }
//       }
//       post = "price=" + price + "format=" + format + "&action=" + method;
      break;
  }
  FillDisplayBooks();
  FillMyBooksTable();

  var checkboxes = document.getElementsByName('batcheditcheck');

  for (var box in checkboxes) {
    for (var id in selectedids) {
      var boxid = "batch" + selectedids[id];
      if (boxid == checkboxes[box].id) {
        checkboxes[box].checked = true;
      }
    }
  }

  var url = "/batchedit?" + post;
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    var xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    var xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.open("GET", url, true);
  xmlhttp.send();
}

// ----------------- Analytics --------------------------

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-37921454-1']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

