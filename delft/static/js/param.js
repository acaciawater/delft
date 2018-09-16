function removeParam(parameter)
{
	var url=document.location.href;
	var urlparts= url.split('?');

	if (urlparts.length>=2)
	{
		var urlBase=urlparts.shift(); 
		var queryString=urlparts.join("?"); 
		
		var prefix = encodeURIComponent(parameter)+'=';
		var pars = queryString.split(/[&;]/g);
		for (var i= pars.length; i-->0;)               
		    if (pars[i].lastIndexOf(prefix, 0)!==-1)   
		        pars.splice(i, 1);
		url = urlBase+'?'+pars.join('&');
		window.history.pushState('',document.title,url); 
	 }
	 return url;
}

function insertParam(key, value)
{
    key = encodeURI(key); 
    value = encodeURI(value);

    var search = document.location.search;
	if (search.length == 0)
		return [key,value].join('=');
    
	var kvp = search.substr(1).split('&');
    var i=kvp.length; 
    while(i--) 
    {
        var x = kvp[i].split('=');

        if (x[0]==key)
        {
            x[1] = value;
            kvp[i] = x.join('=');
            break;
        }
    }

    if(i<0) {
    	kvp[kvp.length] = [key,value].join('=');
    }

    return kvp.join('&'); 
}
