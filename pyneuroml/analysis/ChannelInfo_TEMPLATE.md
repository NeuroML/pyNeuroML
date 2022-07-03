Channel information
===================
    
<p style="font-family:arial">${info}</p>

#foreach ($channel in $channels)##
<div style="border:solid 2px white; padding-left:10px">
<div>
<b>${channel.id}</b><br/>
<a href="../${channel.file}">${channel.file}</a>
     <br/>
        <b>Ion: ${channel.species}</b><br/>
        <b>
        <i><code>${channel.expression}</code></i><br/>
        </b>
        </div>

        ${channel.notes}
<div><a href="${channel.id}.inf.png"><img alt="${channel.id} steady state" src="${channel.id}.inf.png" height="250" width="300" style="padding:10px 35px 10px 0px"/></a>
<a href="${channel.id}.tau.png"><img alt="${channel.id} time course" src="${channel.id}.tau.png" height="250" width="300" style="padding:10px 10px 10px 0px"/></a>
</div>
</div>
#end## 

