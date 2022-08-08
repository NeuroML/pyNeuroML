Channel information
===================

<p style="font-family:arial">${info}</p>

#foreach ($channel in $channels)##

<h2>${channel.id}</h2>

Ion: <b>${channel.species}</b> |
Conductance expression: <b>${channel.expression}</b> |
NeuroML2 file: <a href="../${channel.file}">${channel.file}</a></div>
<details><summary>Notes</summary>${channel.notes}</details>

<div><a href="${channel.id}.inf.png"><img alt="${channel.id} steady state" src="${channel.id}.inf.png" width="350" style="padding:10px 35px 10px 0px"/></a>
<a href="${channel.id}.tau.png"><img alt="${channel.id} time course" src="${channel.id}.tau.png" width="350" style="padding:10px 10px 10px 0px"/></a>
</div>
</div>
#end##
