declare namespace saxon="http://saxon.sf.net/";
declare namespace ud="https://universaldependencies.github.io/docs/" ;

declare option saxon:output "omit-xml-declaration=yes";
declare option saxon:output "indent=yes";

declare  variable $DIR as xs:string external ;

declare  variable $MODE as xs:string external ;

declare function local:add_pos_tags($node as node()) as node() {
  if ($node[@pos])
  then element {name($node)} {($node/@*, local:universal_pos_tag($node))}
  else element {name($node)} {($node/@*, for $child in $node/node return local:add_pos_tags($child))}
};

declare function local:universal_pos_tag($node as element(node)) as attribute() {
  let $POS := $node/@pos
  let $REL := $node/@rel
  return 
  attribute ud:pos {
         if ($POS eq 'punct') then 'PUNCT' 
    else if ($POS eq 'adj')   then 
      if (contains($node/@frame,'wh_adjective')) then 'ADV'
      else if (matches($node/@root,'^(hoe|wel|geleden|alleen)')) then 'ADV'  
      else if (contains($node/@frame,'adjective(meer)')) then 'PRON' 
      else if (matches($node/@root,'meer')) then 'PRON'
      else if (matches($node/@root,'(zoveel|hoeveel|evenveel|teveel)')) then 'NUM'
      else if (matches($node/@root,'(kom|afgelopen|betrokken|besta|betaald|verloren|verwacht|gedwongen|veroordeeld|gesloten|kom_bij|verrassend|beperkt)')) then 'VERB'
      else 'ADJ'
    else if ($POS eq 'adv')   then 
      if (matches($node/@root,'^(heel|ruim|zeker|langer|precies|destijds|degelijk)$')) then 'ADJ'
      else if (matches($node/@frame,'^(intensifier|modal_adverb)')) then 'ADJ'
      else if (matches($node/@root,'^(onder|mee|ten|buiten|binnen|te|met|in|toe|boven|beneden|af|van|tot|bij|op|ter)')) then 'ADP'
      else if (matches($node/@root,'^(dan|wanneer|toen|als)')) then 'SCONJ'
      else 'ADV' 
    else if ($POS eq 'pp')    then 'ADV'
    else if ($POS eq 'det')   then 
      if (matches($node/@frame,'determiner\((pron|onze)')) then 'PRON'
      else if (matches($node/@root,'^(zijn|mijn|hun|haar|je|u|uw|jullie|diens|ons)$')) then 'PRON' 
      else if (matches($node/@root,'^dan$')) then 'SCONJ' 
      else 'DET'
    else if ($POS eq 'prefix')   then 'NOUN'
    else if ($POS eq 'noun')  then
      if (matches($node/@root,'jongere')) then  'ADJ'
      else if (contains($node/@frame,'proper_name')) then  'PROPN' 
      else if (matches($node/@root,'(maan|dins|woens|donder|vrij|zater|zon)dag')) then  'PROPN' 
      else if (matches($node/@root,'(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)')) then  'PROPN' 
      else if (matches($node/@root,'(ja|nee)',"i")) then  'INTJ' 
      else if (matches($node/@root,'[0-9]+')) then  'NUM' 
      else 'NOUN'
    
    else if ($POS eq 'name')  then 
      if (matches($node/@root,'^(!|,|/|-)$')) then 'PUNCT'
      else if (matches($node/@root,'^(de.?|het|een)$',"i")) then 'DET'
      else if (matches($node/@root,'[0-9]+')) then  'NUM'
      else if (matches($node/@root,'en')) then  'CCONJ'
      else 'PROPN'
    else if ($POS eq 'tag')   then 'INTJ'
    else if ($POS eq 'num')   then 'NUM'
    else if ($POS eq 'comparative')  then 'SCONJ'
    else if ($POS eq 'comp')  then 
      if (matches($node/@root,'(om|te|door|aan|voor|tot|van|zonder|sinds|naar|in|met|na)')) then 'ADP'
      else if (matches($node/@root,'(en|maar|want|dus)'))  then  'CCONJ'
      else 'SCONJ'
    else if ($POS eq 'fixed') then 
      if (matches($node/@root,'(in|aan|van|op|te|uit|ten|voor|onder|tot|bij|om|over|tegen|door|af)')) then 'ADP'
      else if (matches($node/@root,'^(de.?|het|een)$')) then 'DET'
      else if (matches($node/@root,'(gewonnen|weten|geroepen)')) then 'VERB'
      else if (matches($node/@root,'klaar')) then 'ADJ' 
      else 'NOUN'  
    else if ($POS eq 'prep')  then 'ADP'  (: v2: do not use PART for SVPs and complementizers :)
    else if ($POS eq 'part')  then 
      if (matches($node/@root,'(terug|weg|vooruit|samen|neer|voort|thuis|overeen|bijeen|tegemoet|uiteen|weer|voorop)')) then 'ADV'
      else 'ADP'
    else if ($POS eq 'pron')  then 'PRON'
    else if ($POS eq 'vg') then 'CCONJ'
    else if ($POS eq 'verb') then 
      if (local:auxiliary($node) eq 'verb') then  'VERB' else  'AUX' (: v2: cop and auxpass --> AUX  (already in place in v1?) :)
    else  'ERROR_NO_POS_FOUND'
    }
};

declare function local:auxiliary($nodes as element(node)*) as xs:string
{ if (count($nodes) = 0)
  then "ERROR_AUXILIARY_FUNCTION_TAKES_EXACTLY_ONE_ARG"
  else local:auxiliary1($nodes[1])
} ;

declare function local:auxiliary1($node as element(node)) as xs:string
{ if ($node[@pos="verb" and @rel="hd" and not(../node[@rel="obj1" or @rel="se"]) and 
                 ( contains(@sc,'copula') or 
                   contains(@sc,'pred')   or   
                   contains(@sc,'cleft')  or 
                   ../node[@rel="predc"] 
                 ) ] )                                
  then "cop"    
  else if ( $node[@pos="verb" and @rel="hd" and (@root="ben" or @root="word") and 
                  ( @sc="passive"  or 
                    ../node[@rel="su"]/@index = ../node[@rel="vc"]/node[@rel="obj1"]/@index or 
                    not(../node[@rel="su"])  
                  ) ] )           
  then "aux:pass"    
  else if ($node[@pos="verb" and @rel="hd" and
                 ( starts-with(@sc,'aux') or
                   ( ../node[@rel="vc"  and   
                             ( @cat="ppart" or @cat="inf" or @cat="ti" or 
                               ( @cat="conj" and node[@rel="cnj" and (@cat="ppart" or @cat="ti" or @cat="inf")] )
                             )  ]   and  
                    (@root="ben" or @root="heb" or @root="zal" or @root="mag" or 
                        @root="hoef" or @root="kan" or @root="ga" or @root="laat" or @root="wil" or @root="blijk") 
                   ) ) ]  )                           
  then "aux"    
  else if ($node[@pos="verb"] )
  then "verb"
  else "ERROR_NO_VERB"
};

declare function local:add_features($node as node()) as node() {
  if      ($node[@ud:pos="NOUN" or @ud:pos="PROPN"])
  then    element {name($node)} {($node/@*, local:nominal_features($node))}
  
  else if ($node[@ud:pos="ADJ"]) 
  then    element {name($node)} {($node/@*, local:adjective_features($node))}
  
  else if ($node[@ud:pos="PRON"] )
  then    element {name($node)} {($node/@*, local:pronoun_features($node))}
       
  else if ($node[@ud:pos="VERB" or @ud:pos="AUX"] )
  then    element {name($node)} {($node/@*, local:verbal_features($node))}
       
  else if ($node[@ud:pos="DET"] )
  then    element {name($node)} {($node/@*, local:determiner_features($node))}  
  

  else if ($node[@ud:pos="X"] )
  then    element {name($node)} {($node/@*, local:special_features($node))}  
  
       
  else    element {name($node)} {($node/@*, for $child in $node/node return local:add_features($child))}
};

declare function local:special_features($node as element(node)) as attribute()+ { 
	( attribute ud:Foreign {
		if ($node/@spectype="vreemd")
		then "Yes"
		else "null"
	}
	,
	  attribute ud:Abbr {
	  	if ($node/@spectype="afk")
	  	then "Yes"
	  	else "null"
	  }
    )
};

declare function local:nominal_features($node as element(node)) as attribute()+ {
  let $GENUS := $node/@gen
  let $GETAL := $node/@num
  let $DEGREE := $node/@root
  return 
  ( attribute ud:Gender {
    if      ($GENUS eq 'de')   then 'Com' 
    else if ($GENUS eq 'het')  then 'Neut'
    else if ($GENUS eq 'both') then 'Com,Neut'
    else if ($GENUS)           then 'ERROR_IRREGULAR_GENDER'
    else                            'null'
    }
  ,
  attribute ud:Number {
    if      ($GETAL eq 'sg')        then 'Sing' 
    else if ($GETAL eq 'pl')        then 'Plur'
    else if ($GETAL eq 'both')      then 'Sing,Plur'
    else if ($GETAL eq 'bare_meas') then 'Sing'
    else if ($GETAL eq 'meas')      then 'Sing'
    else if ($GETAL)                then 'ERROR_IRREGULAR_NUMBER'
    else                            'null'
    }
  ,
  attribute ud:Degree {
    if      (contains($DEGREE,'_DIM'))  then 'null'
    else if ($DEGREE)                   then 'null'
    else                                'null'
    }
  )
};

declare function local:adjective_features($node as element(node)) as attribute()+ {
  let $GRAAD := $node/@frame
  return 
  attribute ud:Degree
    {
    if      (contains($GRAAD,'adjective(e)'))       then 'Pos'
    else if (contains($GRAAD,'adjective(both'))     then 'Pos'
    else if (contains($GRAAD,'adjective(no_e'))     then 'Pos'
    else if (contains($GRAAD,'adjective(pred'))     then 'Pos'
    else if (contains($GRAAD,'adjective(end'))      then 'Pos'
    else if (contains($GRAAD,'anders'))             then 'Pos'
    else if (contains($GRAAD,'adjective(er'))       then 'Cmp'
    else if ($GRAAD eq 'adjective(meer)')           then 'Cmp'
    else if (contains($GRAAD,'adjective(st'))       then 'Sup'
    else if (contains($GRAAD,'adjective(het_st'))   then 'Sup'
    else if ($GRAAD eq 'dim')                       then 'Pos' (: netjes :) 
    (: else if ($GRAAD)                                then 'ERROR_IRREGULAR_DEGREE' :)
    else if ($GRAAD)                                then 'Pos'
    else                                            'null'
    }
};

declare function local:pronoun_features($node as element(node)) as attribute()+ {
  let $VWTYPE  := $node/@frame
  let $DEFIN   := $node/@def
  let $PERSOON := $node/@per
  let $NAAMVAL := $node/@case
  return 
  ( attribute ud:PronType {
    if      (contains($VWTYPE ,'pronoun(nwh'))                         then 'Prs'
    else if ($VWTYPE eq 'determiner(pron)')                            then 'Prs'
    else if ($VWTYPE eq 'reflexive(u_thi,both)')                       then 'Prs'
    else if (contains($VWTYPE,'pronoun(nwh,thi,both,de,dat_acc,def'))  then 'Prs'
    else if ($VWTYPE eq 'reflexive(u_thi,both)')                       then 'Prs'
    else if (contains($VWTYPE,'de,dat_acc,def'))                       then 'Prs'
    else if (contains($VWTYPE,'reflexive(fir,'))                       then 'Prs'
    else if (contains($VWTYPE,'reflexive(je,'))                        then 'Prs'
    else if ($VWTYPE eq 'pronoun(nwh,thi,pl,de,dat_acc,def)')          then 'Rcp'
    else if (contains($VWTYPE,'pronoun(ywh,thi'))                      then 'Int'
    else if ($VWTYPE eq 'rel_pronoun(het,both)')                       then 'Int'
    else if ($VWTYPE eq 'rel_pronoun(both,obl)')                       then 'Int'
	else if ($VWTYPE eq 'rel_pronoun(de,obl)')                         then 'Rel,Dem'
    else if ($VWTYPE eq 'rel_pronoun(de,no_obl)')                      then 'Rel,Dem'
    else if ($VWTYPE eq 'rel_pronoun(het,no_obl)')                     then 'Rel,Dem'
    else if ($DEFIN eq 'indef')                                        then 'Ind'
    else if ($VWTYPE eq 'adjective(meer)')                             then 'Ind'
    else if ($VWTYPE)                                                  then 'ERROR_IRREGULAR_PRONTYPE'
    else                                                               'null'
    }
    ,
    attribute ud:Reflex {
    if (contains($VWTYPE,'reflexive(u_thi,both)')) 	then 'Yes'
    else 			     'null'
    }
    ,
    attribute ud:Poss {
    if (contains($VWTYPE,'pronoun(nwh,fir,pl,de,dat_acc,def)')) 	then 'Yes'
    else if (contains($VWTYPE,'pronoun(nwh,je,sg,de,both,def,wkpro)')) 	then 'Yes'
    else 			     'null'
    }
    ,
    attribute ud:Person {
    if      ($PERSOON eq 'fir')     then '1'
    else if ($PERSOON eq 'je')      then '2'
    else if ($PERSOON eq 'u')       then '2'
    else if ($PERSOON eq 'thi')     then '3'
    else if ($PERSOON eq 'u_thi')   then '3'
    else if ($PERSOON)              then 'ERROR_IRREGULAR_PERSON'
    else                            'null'
    }
    ,
    attribute ud:Case {
    if    ($NAAMVAL eq 'nom')        then 'Nom'
    else if ($NAAMVAL eq 'dat_acc')  then 'Acc'
    else if ($NAAMVAL eq 'gen')      then 'Gen'
    else if ($NAAMVAL eq 'dat')      then 'Dat' (: van dien aard :) 
    else if ($NAAMVAL eq 'both')     then 'null'
    else if ($NAAMVAL eq 'no_obl')   then 'null'
    else if ($NAAMVAL eq 'obl')      then 'null'
    else if ($NAAMVAL)               then 'ERROR_IRREGULAR_CASE'
    else                             'null'
    }
  )
};

declare function local:verbal_features($node as element(node)) as attribute()+ {
  let $WVORM  := $node/@infl
  let $PVTIJD := $node/@infl
  let $PVAGR  := $node/@infl
  return 
  ( attribute ud:VerbForm   {
    if      (contains($WVORM,'sg'))     then 'Fin'
    else if (contains($WVORM,'pl'))     then 'Fin'
    else if (contains($WVORM,'modal_')) then 'Fin'
    else if ($WVORM eq 'subjunctive')   then 'Fin'
    else if ($WVORM eq 'inf')           then 'Inf'
    else if ($WVORM eq 'inf(no_e)')     then 'Inf'
    else if ($WVORM eq 'psp')           then 'Part'
    else if ($WVORM)                    then 'ERROR_IRREGULAR_VERBFORM'
    else                                'null'
    }
    ,
    attribute ud:Tense {
    if      (contains($PVTIJD,'past'))   then 'Past'
    else if ($PVTIJD eq 'sg')            then 'Pres'
    else if ($PVTIJD eq 'sg1')           then 'Pres'
    else if ($PVTIJD eq 'sg3')           then 'Pres'
    else if ($PVTIJD eq 'sg_hebt')       then 'Pres'
    else if ($PVTIJD eq 'sg_heeft')      then 'Pres'
    else if (contains($PVTIJD,'modal_')) then 'Pres'
    else if ($PVTIJD eq 'subjunctive')   then 'Pres'
    else if ($PVTIJD eq 'pl')            then 'Pres'
    (: else if ($PVTIJD)                 then 'ERROR_IRREGULAR_TENSE' :)
    else                                 'null'
    }
    ,
    attribute ud:Number {
    if      (contains($PVAGR,'sg'))     then 'Sing'
    else if ($PVAGR eq 'subjunctive')   then 'Sing'
    else if (contains($PVAGR,'modal_')) then 'Sing'
    else if (contains($PVAGR,'pl'))     then 'Plur'
    (: else if ($PVAGR)                 then 'ERROR_IRREGULAR_NUMBER' :)
    else                                'null'
    }
  )
};

declare function local:determiner_features($node as element(node)) as attribute()+ {
  let $LWTYPE := $node/@infl
  return 
  attribute ud:Definite
    {
    if      (matches($LWTYPE,'^de'))   then 'Def' 
    else if ($LWTYPE eq 'het')         then 'Def'
    else if (matches($LWTYPE,'(een|geen|wat|al|enkele|zulk)'))         then 'Ind'
    else if (contains($LWTYPE,'pl'))   then 'Ind'
    else if ($LWTYPE)                  then 'ERROR_IRREGULAR_DEFINITE'
    else                              'null'
    }
};


declare function local:add_dependency_relations($node as node()) as node() {
  if ($node[@pos])
  then element {name($node)} {($node/@*, local:dependency_relation($node))}
  else element {name($node)} {($node/@*, for $child in $node/node return local:add_dependency_relations($child))}
};

(: used for debugging, but also nice as readible alternative for selecting by [1] or by means of @begin position :)
declare function local:leftmost($nodes as element(node)*) as element(node) {
	let $sorted :=  for $node in $nodes
	                order by number($node/@begin)
	                return $node
	return
	    $sorted[1]
};

declare function local:dependency_relation($node as element(node)) as attribute()+ {
  ( attribute ud:Relation {
    local:dependency_label($node)
    }
    ,
    attribute ud:HeadPosition {
    if ($node[@rel="hd" and @ud:pos="ADP"] ) 
    then  if ($node/../node[@rel= ("obj1","vc","se","me")] ) 
          then     local:internal_head_position(($node/../node[@rel= ("obj1","vc","se","me")])[1])
          else if ($node/../node[@rel="predc"] ) (: met als titel :)
               then     local:internal_head_position(($node/../node[@rel="predc"])[1])
               else if ($node/../node[@rel="pobj1"] )
                    then local:internal_head_position(($node/../node[@rel="pobj1"])[1] )
                        (: in de eerste rond --> typo in LassySmall/Wiki , binnen en [advp later buiten ]:)
                    else if ($node[../@cat=("ap","ppart","np","advp")])    
                         then local:external_head_position($node/..)
                         else "ERROR_NO_HEAD_FOUND"
    
   

    else if ($node[@rel="hd" and  local:auxiliary($node) eq 'aux:pass' and ../node[@rel="vc"]])
    then     local:internal_head_position(($node/../node[@rel="vc"])[1])
    
    else if ($node[@rel="hd"] and local:auxiliary($node) eq 'aux' and $node/../node[@rel="vc"])
    then     local:internal_head_position(($node/../node[@rel="vc"])[1])
    
    else if ($node[@rel="hd" and local:auxiliary($node) eq 'cop'  and $node/../node[@rel="predc"]])
    then     local:internal_head_position(($node/../node[@rel="predc"])[1])
    
    else if ($node[@rel=("obj1","pobj1","se","me") and (../@cat="pp" or ../node[@rel="hd" and @ud:pos="ADP"])])   (: op zich nemen :)
    then     local:external_head_position($node/..)

    else if ($node[@rel="mod" and not(../node[@rel=("obj1","pobj1","se","me")]) and (../@cat="pp" or ../node[@rel="hd" and @ud:pos="ADP"])])   (: mede op grond hiervan :)
    then     local:external_head_position($node/..)
    
    
    else if ($node[@rel=("cnj","dp","mwp")])
    then if ( (: deep-equal($node,$node/../node[@rel=$node/@rel][1]) :)
              not($node/../node[(@cat or @pos) and @rel=("cnj","dp","mwp")]/number(@begin) < $node/number(@begin))
            ) 
         then    local:external_head_position($node/..)
         else    local:internal_head_position($node/..)   
         
    else if ($node[@rel="cmp" and ../node[@rel="body"]])
    then    local:internal_head_position($node/../node[@rel="body"][1])
         
    else if ( $node[@rel="--"] )
         then if ($node[@ud:pos = ("PUNCT","SYM","X","CONJ","NOUN","PROPN","NUM","ADP","ADV","DET","PRON") 
                         and ../node[@rel="--" and 
                                     not(@ud:pos=("PUNCT","SYM","X","CONJ","NOUN","PROPN","NUM","ADP","ADV","DET","PRON")) ] ] ) 
              then    local:internal_head_position($node/../node[@rel="--" and not(@ud:pos=("PUNCT","SYM","X","CONJ","NOUN","ADP","ADV","DET","PROPN","NUM","PRON"))][1])
              else if ( $node/../node[@cat]  ) 
              then    local:internal_head_position($node/../node[@cat][1])
              else if ($node[@ud:pos="PUNCT" and count(../node) > 1]) 
              then if ($node/../node[not(@ud:pos="PUNCT")] )
                   then local:internal_head_position($node/../node[not(@ud:pos="PUNCT")][1])
                   else if ( $node[@begin=../@begin] ) 
                        then local:external_head_position($node/..)
                        else "1" (: ie end of first punct token :)
              else if ($node/..) then local:external_head_position($node/..)
                   else "ERROR_NO_HEAD_FOUND"
         
    else if ($node[@rel=("hd","nucl","body") ] ) 
    then    local:external_head_position($node/..)
       
    else if ( $node[@rel="predc"] ) 
         then if   ($node/../node[@rel=("obj1","se")] and $node/../node[@rel="hd"] )
              then if ( $node/../node[@rel="hd" and @ud:POS="ADP"] ) 
                   then local:internal_head_position($node/../node[@rel=("obj1","se")]) (: met als presentator Bruno W :)
                   else local:internal_head_position($node/../node[@rel="hd"])
              else if  ( $node/..[@cat="np" and node[@rel="hd" and (@cat or @word) and not(@ud:pos=("COP","AUX") ) ]  ]  )  (: reduced relatives , make sure head is not empty (ellipsis) :)
                   then local:internal_head_position($node/../node[@rel="hd"])
                   else local:external_head_position($node/..)
             
    else if ($node[@rel="vc"]) 
       then if ($node/../node[@rel="hd" and @ud:pos="AUX"] and not($node/../node[@rel="predc"]) )
            then local:external_head_position($node/..)
            else if ($node/../node[@rel="hd" and @ud:pos="ADP"])
                 then local:external_head_position($node/..)
            else local:internal_head_position($node/..)

    else if ($node[@rel="whd" or @rel="rhd"])
    then if ($node[@index]) 
         then local:external_head_position( ($node/../node[@rel="body"]//node[@index = $node/@index ])[1] ) 
         else local:internal_head_position($node/../node[@rel="body"])
    
    else if ( $node/..  ) 
    then    local:internal_head_position($node/..)
         
    else "ERROR_NO_HEAD_FOUND"
    }
  )
} ;

declare function local:internal_head_position($nodes as element(node)*) as xs:string
{ if ( count($nodes) = 1 )
  then local:internal_head_position1($nodes[1])
  else "ERROR_ZERO_OR_MORE_THAN_ONE_INTERNAL_HEAD_POSITION_FOUND"
} ;

declare function local:internal_head_position1($node as element(node)) as xs:string
{ if      ($node[@cat="pp"])
  then    if ($node/node[@rel="hd" and @pos=("adv","noun")] )  (: n --> TEMPORARY HACK to fix error where NP is erroneously tagged as PP :)
          then $node/node[@rel="hd"]/@end
          else if ($node/node[@rel="obj1" or @rel="pobj1" or @rel="se"]) 
               then local:internal_head_position($node/node[@rel="obj1" or @rel="pobj1" or @rel="se"][1])
               else local:internal_head_position( $node/node[1] )    
  
  else if ($node[@cat="mwu"] ) 
  then    $node/node[@rel="mwp" and not(../node/number(@begin) < number(@begin))]/@end
  
  else if ($node[@cat="conj"])
  then    local:internal_head_position(local:leftmost($node/node[@rel="cnj"]))
  
  else if ( $node/node[@rel="predc"] ) 
        then if   ($node[node[@rel=("obj1","se")] and node[@rel="hd"]])
             then local:internal_head_position($node/node[@rel="hd"])
             else if  ( $node[@cat="np" and node[@rel="hd" and not(@ud:pos=("COP","AUX") ) ]  ]  )  (: reduced relatives :)
             then local:internal_head_position($node/node[@rel="hd"])
             else local:internal_head_position($node/node[@rel="predc"])
  
  else if ($node/node[@rel="vc"] and $node/node[@rel="hd" and @ud:pos="AUX"] )
  then    local:internal_head_position($node/node[@rel="vc"])
   
  else if ( $node/node[@rel="hd"]) 
  then    local:internal_head_position($node/node[@rel="hd"][1])
  
  else if ( $node/node[@rel="body"]) 
  then    local:internal_head_position($node/node[@rel="body"][1])
  
  else if ( $node/node[@rel="dp"]) 
  then    local:internal_head_position(local:leftmost($node/node[@rel="dp"]))
       (: sometimes co-indexing leads to du's starting at same position ... :)

  else if ( $node/node[@rel="nucl"]) 
  then    local:internal_head_position($node/node[@rel="nucl"][1])

  else if ( $node/node[@cat="du"]) (: is this neccesary at all? , only one referring to cat, and causes problems if applied before @rel=dp case... :)
  then    local:internal_head_position($node/node[@cat ="du"][1])

  else if ( $node[@word] )
  then    $node/@end
  
  else if ($node[@index and not(@word or @cat)] )
  then    local:internal_head_position($node/ancestor::*//node[@index = $node/@index and (@word or @cat)] )
  
  
  else    'ERROR_NO_INTERNAL_HEAD'
};

declare function local:external_head_position($nodes as element(node)*) as xs:string
{ if (count($nodes) = 0 ) 
  then "ERROR_EXTERNAL_HEAD_MUST_HAVE_ONE_ARG"
  else local:external_head_position1($nodes[1]) 
} ;

declare function local:external_head_position1($node as element(node)) as xs:string
{ if      ( $node[@rel=("hd","body","nucl")] ) 
  then    local:external_head_position($node/..)
  
  else if ($node[@rel="predc"] )
        then if   ($node/../node[@rel=("obj1","se")] and $node/../node[@rel="hd"])
             then local:internal_head_position($node/../node[@rel="hd"])
             else if  ( $node/..[@cat="np" and node[@rel="hd" and (@cat or @word) and not(@ud:pos=("COP","AUX") ) ]  ]  )  (: reduced relatives , check head is not empty :)
             then local:internal_head_position($node/../node[@rel="hd"])
             else local:external_head_position($node/..)


  else if ( $node[@rel=("obj1","pobj1","me") and (../@cat="pp" or ../node[@ud:pos="ADP" and @rel="hd"])] )
  then    local:external_head_position($node/..)
  
  else if ($node[@rel=("cnj","dp","mwp")])
    then if ( (: deep-equal($node,$node/../node[@rel=$node/@rel][1]) :)
              (: not($node/../node[(@cat or @pos) and @rel=("cnj","dp","mwp")]/number(@begin) < $node/number(@begin)) :)
              deep-equal($node,local:leftmost($node/../node[@rel=("cnj","dp","mwp")]))
            ) 
            then local:external_head_position($node/..)
            else local:internal_head_position($node/..)
            
  else if ($node[@rel="--" and not(@ud:pos="PUNCT")])
       then   if      ( $node[@cat="mwu"]/../node[@cat and not(@cat="mwu")]  )    (: fix for multiword punctuation in Alpino output :)
              then    local:internal_head_position($node/../node[@cat and not(@cat="mwu")][1])
              else    local:external_head_position($node/..)

  else if ($node[@rel=("dlink","sat","tag")])
       then if ($node/../node[@rel="nucl"])
             then local:internal_head_position($node/../node[@rel="nucl"])
             else "NO_EXTERNAL_HEAD"
   
  else if ($node[@rel="vc"]) 
       then if ($node/../node[@rel="hd" and @ud:pos="AUX"] and not($node/../node[@rel="predc"]) )
            then local:external_head_position($node/..)
            else if ($node/../node[@rel="hd" and @ud:pos="ADP"])
                 then local:external_head_position($node/..)
            else local:internal_head_position($node/..)
            
  else if ($node[@rel="whd" or @rel="rhd"]) 
       then if ($node[@index])
            then local:external_head_position( ($node/../node[@rel="body"]//node[@index = $node/@index ])[1] )
            else local:internal_head_position($node/../node[@rel="body"])

  else if ($node[@rel="top"]) then "0"
  
  else if ( $node[not(@rel="hd")] )
  then    local:internal_head_position($node/..)
  
  else    'ERROR_NO_EXTERNAL_HEAD'
} ;


declare function local:dependency_label($node as element(node)) as xs:string
{   if      ($node/..[@cat="top" and @end="1"])     then "root" 
    else if ($node[@rel="app"])                     then "appos"
    else if ($node[@rel="cmp"])                     then "mark"
    else if ($node[@rel="crd"])                     then "cc"
    else if ($node[@rel="me" and not(../node[@ud:pos="ADP"]) ])   then local:determine_nominal_mod_label($node)
    else if ($node[@rel="obcomp"])                  then "advcl"
    else if ($node[@rel="obj2"])                    then "iobj"
    else if ($node[@rel="pobj1"])                   then "expl"
    else if ($node[@rel="predc"]) 
         then if ( not ($node/../node[@rel="obj1" or @rel="se"] or $node/../node[@rel="hd" and not(@ud:pos="AUX")]) ) then local:dependency_label($node/..) else "xcomp"   
         (: hack for now: de keuze is gauw gemaakt :)
         (: was amod, is this more accurate?? :)
         (: examples of secondary predicates under xcomp suggests so :)
    else if ($node[@rel="se"])                      then "obj"
    else if ($node[@rel="su"])  					then local:subject_label($node)
    else if ($node[@rel="sup"])                     then "expl"
    else if ($node[@rel="svp"])                     then "compound:prt"  (: v2: added prt extension:)
    else if (local:auxiliary($node) eq 'aux:pass')  then "aux:pass"                                                
    else if (local:auxiliary($node) eq 'aux')       then "aux"    
    else if (local:auxiliary($node) eq 'cop')       then "cop"    
  
    
    else if ( $node[@rel="det"] ) 
         then if ( $node/@ud:pos = ("DET","PROPN","NOUN","ADJ","PRON","ADV","X")  ) then "det"   (: meer :)(: genoeg :) (:the :)
         else if ( $node/@cat = ("mwu","np","pp","ap","detp","smain") )                 then "det" 
         (: tussen 5 en 6 .., needs more principled solution :)
         (: nog meer mensen dan anders  :)
         (: hetzelfde tijdstip als anders , nogal wat, :)
         (: hij heeft ik weet niet hoeveel boeken:)
         else if ( $node/@ud:pos = ("NUM","SYM") )           then "nummod"
         else if ( $node[@cat="conj"]) 
              then if ($node/node[@rel="cnj"][1]/@ud:pos="NUM" )
                   then "nummod"
                   else "det"
      
                                                    else "ERROR_NO_LABEL_DET"
              
    else if ($node[@rel="obj1" or @rel="me"] )
         then if ( $node/../node[@rel="hd" and @ud:pos="ADP"] )
              then local:dependency_label($node/..)  
	      else "obj"
						    
    else if ($node[@rel="mwp"])
         then if ($node[@begin = ../@begin])
              then local:dependency_label($node/..)
(:              else  if ( $node[@spectype="deeleigen"] )   
                                                    then "name"	         
						    else "mwe"
						    :)
			    else if ( $node/../node[@ud:pos="PROPN"]) 
			         then "flat:name"  (: v2: name --> flat:name :)
			         else "fixed"   (: v2 mwe-> fixed :)
						    
    else if ($node[@rel="cnj"])    
         then if   (deep-equal($node,$node/../node[@rel="cnj"][1]))
              then local:dependency_label($node/..)
              else                                       "conj"       
              
     else if ($node[@rel="dp"])    
         then if   (deep-equal($node,$node/../node[@rel="dp"][1]))
              then local:dependency_label($node/..)
              else                                      "parataxis"      
    else if ($node[@rel="tag"] )                   then "parataxis"
    
    else if ($node[@rel="sat"] )                   then "parataxis"
    
    else if ($node[@rel="dlink"])                  then "mark"
    
    else if ($node[@rel="nucl"]) 
         then  local:dependency_label($node/..)
    					    					    						   					    
    else if ($node[@rel="vc"] ) 
         then if ($node/../node[@rel="hd" and @ud:pos="AUX"] and not($node/../node[@rel="predc"]) )
              then local:dependency_label($node/..)
              else if ($node/../node[@rel="hd" and @ud:pos="ADP"])
              	   then local:dependency_label($node/..)
              	   else if ($node/node[@rel="su" and @index and not(@word or @cat)] )
                        then "xcomp"                                    
                       	else if ($node/../@cat="np") 
                       	     then "acl"               (: v2: clausal dependents of nouns always acl :)
                       	     else "ccomp"     
    
    else if ($node[@rel=("mod","pc","ld") and ../@cat="np"])  (: [detp niet veel] meer :) 
         (: modification of nomimal heads :)
         (: pc and ld occur in nominalizations :)
         then if ($node[@cat="pp"]/node[@rel="vc"]) then "acl"  (: pp containing a clause :) 
         else if ($node[@cat=("pp","np","conj","mwu") or @ud:pos=("NOUN","PRON","PROPN","X","PUNCT","SYM","INTJ") ]) then "nmod"
         else if ($node[@ud:pos="ADJ" or @cat="ap"])   then "amod"
         else if ($node[@ud:pos="NUM"])                then "nummod"
         else if ($node[@cat="detp"])                then "det" (: [detp niet veel] meer error? :)
         else if ($node[@cat=("rel","whrel")])         then "acl:relcl"  
                (: v2 added relcl -- whrel= met name waar ... :)
         else if ($node[@cat="cp"]/node[@rel="body" and (@ud:pos = ("NOUN","PROPN") or @cat=("np","conj"))] ) then "nmod"   
                (: zijn loopbaan [CP als schrijver] :) 
         else if ($node[@cat=("cp","sv1","smain","ppres","ppart","ti","oti","du","whq") or @ud:pos="SCONJ"])  then "acl" 
                (: oa zinnen tussen haakjes :)
         else if ($node[@ud:pos= ("ADV","ADP","VERB","CCONJ") or @cat="advp"])  then "amod"
               (: VERB= aanstormend etc -> amod, ADV = nagenoeg alle prijzen, slechts 4 euro --> amod :)
               (: CCONJ = opdrachten zoals:   --> amod :)
         else if ($node[@index])     then "ERROR_INDEX_NMOD"
         else                        "ERROR_NO_LABEL_NMOD"
         
    else if ($node[@rel=("mod","pc","ld") and ../@cat=("sv1","smain","ssub","inf","ppres","ppart","oti","ap","advp")]) 
         (: modification of verbal, adjectival heads :)
         (: nb some oti's directly dominate (preceding) modifiers :)
         (: [advp weg ermee ] :)
         then if ($node[@cat="pp"]/node[@rel="vc"] ) then "advcl"
         else if ($node[@cat=("pp","np","conj","mwu") or @ud:pos=("NOUN","PRON","PROPN","X","PUNCT","SYM") ]) then "obl"
         else if ($node[@cat=("cp","sv1","smain","ppres","ppart","ti","oti","du","whq","whrel","rel")])  then "advcl"
         else if ($node[@ud:pos= ("ADJ","ADV","ADP","VERB","SCONJ","INTJ") or @cat=("advp","ap")])  then "advmod"
         else if ($node[@ud:pos="NUM"])    then "nummod"
         else if ($node[@index])           then "ERROR_INDEX_VMOD"
         else                              "ERROR_NO_LABEL_VMOD"

    else if ($node[@rel="mod" and ../@cat=("pp","detp","advp")])
         then "amod"

    else if ($node[@rel="mod" and ../@cat=("cp", "whrel", "whq", "whsub")])
         (: [cp net  [cmp als] [body de Belgische regering]], net wat het land nodig heeft :)
         then if ($node/../node[@rel="body"]/node[@rel="hd" and @ud:pos="VERB"])
              then "advmod"
              else "amod"
         
    else if ($node[@rel="hdf"])   then "case"
         
    else if ($node[@rel="predm"])
         then if ($node[@ud:pos])                      then "advmod"
         else                                               "advcl"
         
         
    else if ( $node[@rel=("rhd","whd")] ) 
         then if ( $node/../node[@rel="body"]//node/@index = $node/@index ) 
              then local:non_local_dependency_label($node,($node/../node[@rel="body"]//node[@index = $node/@index])[1])
              else "advmod"  (: [whq waarom jij] :)                                                                             
       
    else if ($node[@rel="body"])
         then local:dependency_label($node/..)
         
    else if ($node[@rel="--"])
         then if ($node[@ud:pos="PUNCT"] )             
              then if ($node[not(../node[not(@ud:pos="PUNCT")]) and @begin=../@begin]) then "root" (:just punctuation :)
              else "punct"   
         else if ($node[@ud:pos="SYM" or @ud:pos="X"] )               
              then if ($node/../node[@cat]) then "appos"  (: 1. Jantje is ziek  1-->appos?? :)
                   else "root"       
         else if ($node[@root="\\"] )                 then "punct"  (: hack for tagging errors in lassy small 250 :)
  (:       else if ($node[contains(@frame,'proper_name')] )       then "punct" :) (: hack for tagging errors in lassy small 250 :)   
         else if ($node[@ud:pos="NUM" and ../node[@cat] ] )  then "parataxis" (: dangling number 1. :)
         else if ($node[@ud:pos="CCONJ" and ../node[@cat="smain" or @cat="conj"]] ) then "cc" 
         (: sentence initial or final 'en' :)
         else if ($node[(@ud:pos="NOUN" or @ud:pos="PROPN" or @ud:pos="VERB") and ../node[@cat="du" or @cat="smain"]] ) then "parataxis" (: dangling words :)
         else if (count($node/../node[not(@ud:pos="PUNCT" or @ud:pos="SYM" or @ud:pos="X")]) < 2 ) then "root" (: only one non-punct/sym/foreign element in the string :)
         else if ($node[@cat="mwu"])
              then if ($node[@begin = ../@begin and @end = ../@end]) 
                   then "root"
                   else if ($node/node[@ud:pos="PUNCT"]) (: fix for mwu punctuation in Alpino output :)
                        then  "punct"
                        else "NO_LABEL_--"
         else if ($node[not(@ud:pos)]/../@rel="top")   then "root"
         else if ($node[@ud:pos="PROPN" and not(../node[@cat]) ] ) then "root"   (: Arthur . :)
         else if ($node[@ud:pos=("ADP","ADV","ADJ","DET","PRON","CCONJ","NOUN","VERB")] )               then "parataxis"
         else "ERROR_NO_LABEL_--"
    
    else if ($node[@rel="hd"])
         then if ($node[@ud:pos="ADP" and not(../node[@rel="pc"]) ] )                then "case"   (: er blijft weinig over van het lijk : over heads a predc and has pc as sister  :)
              else local:dependency_label($node/..)
              
    else    					        "ERROR_NO_LABEL"
};

declare function local:non_local_dependency_label($head as element(node), $gap as element(node)) as xs:string 
{ if      ($gap[@rel="su"])    then "nsubj"
  else if ($gap[@rel="obj1"])  then "obj"
  else if ($gap[@rel="obj2"])  then "iobj"
  else if ($gap[@rel="me"  ])  then local:determine_nominal_mod_label($gap)
  else if ($gap[@rel="predc"]) then local:dependency_label($gap/..)
  else if ($gap[@rel= ("pc", "ld")] )
       then if ($head/node[@rel="obj1"])                       then "nmod"
            else if ($head[@ud:pos=("ADV", "ADP") or @cat=("advp","ap")])    then "advmod" (: waar precies zit je .. :)
            else "ERROR_NO_LABEL_INDEX_PC"
  else if ($gap[@rel="pobj1"]) then "expl"   (: waar het om gaat is dat hij scoort :) 
  else if ($gap[@rel="mwp"]) then local:dependency_label($gap/..)   (: wat heb je voor boeken gelezen :)
  else if ($gap[@rel="vc"]) then "ccomp"   (: wat ik me afvraag is of hij komt -- CLEFT:)
  else if ($gap[@rel="mod"]) 
       then if ($head[@cat=("pp","np") or @ud:pos=("NOUN","PRON")])                    then "nmod"
       else if ($head[@ud:pos=("ADV","ADP") or @cat= ("advp","ap","mwu","conj")]) then "advmod" (: hoe vaak -- AP, daar waar, waar en wanneer, voor als rhd :)
            else "ERROR_NO_LABEL_INDEX_MOD"
  else if ($gap[@rel="hd"] and $head[@ud:pos=("ADP","ADV")]) (: waaronder A, B, en C :)
       then "case"
  else if ($gap[@rel=("du","dp")]) then "parataxis"
  else "ERROR_NO_LABEL_INDEX"
};

declare function local:determine_nominal_mod_label($node as element(node)) as xs:string
{ if ($node/../node[@rel="hd" and (@ud:pos="VERB" or @ud:pos="ADJ")]) 
  then "obl"
  else "nmod"
};

declare function local:determine_adjectival_mod_label($node as element(node)) as xs:string
{ if ($node/../node[@rel="hd" and (@ud:pos="VERB" or @ud:pos="ADJ")]) 
  then "obl"
  else "amod"
};

declare function local:subject_label($subj as element(node)) as xs:string 
{ let $cat := if   ( $subj[@cat=("whsub","ssub","ti","cp","oti")] or 
                     $subj[@cat="conj" and node/@cat=("whsub","ssub","ti","cp","oti")]
	                ) 
              then "csubj" 
              else "nsubj"
  let $pass := local:passive_subject($subj) 
  return string-join(($cat,$pass),"")
};

declare function local:passive_subject($subj as element(node)) as xs:string 
{   if ( local:auxiliary(($subj/../node[@rel="hd"])[1]) eq "aux:pass" ) (: de carriere had gered kunnen worden :)
    then ":pass" 
    else if (local:auxiliary(($subj/../node[@rel="hd"])[1]) eq "aux"  and 
             $subj/@index = $subj/../node[@rel="vc"]/node[@rel="su"]/@index
            )
         then local:passive_subject($subj/../node[@rel="vc"]/node[@rel="su"])
         else ""
};

declare function local:conll-attribute($value as xs:string, $attribute as xs:string) as xs:string {
  if ($value eq 'null') 
  then "" 
  else string-join(($attribute,$value),"=")
};

declare function local:conll($node as element(node)) as xs:string*
{
for $word in $node//node[@word]

let $degree := if ($word/@ud:Degree)
               then local:conll-attribute($word/@ud:Degree,"Degree")
               else ""       
let $case   := if ($word/@ud:Case)
               then local:conll-attribute($word/@ud:Case,"Case")
               else ""
let $gender := if ($word/@ud:Gender)
               then local:conll-attribute($word/@ud:Gender,"Gender")
               else ""
let $person := if ($word/@ud:Person)
               then local:conll-attribute($word/@ud:Person,"Person")
               else ""
let $prontype := if ($word/@ud:PronType)
               then local:conll-attribute($word/@ud:PronType,"PronType")
               else ""
let $number := if ($word/@ud:Number)
               then local:conll-attribute($word/@ud:Number,"Number")
               else ""
let $reflex := if ($word/@ud:Reflex)
               then local:conll-attribute($word/@ud:Reflex,"Reflex")
               else ""
let $poss   := if ($word/@ud:Poss)
               then local:conll-attribute($word/@ud:Poss,"Poss")
               else ""
let $verbform := if ($word/@ud:VerbForm)
               then local:conll-attribute($word/@ud:VerbForm,"VerbForm")
               else ""
let $tense  := if ($word/@ud:Tense)
               then local:conll-attribute($word/@ud:Tense,"Tense")
               else ""
let $definite := if ($word/@ud:Definite)
               then local:conll-attribute($word/@ud:Definite,"Definite")
               else ""
let $foreign := if ($word/@ud:Foreign)
               then local:conll-attribute($word/@ud:Foreign,"Foreign")
               else ""
let $abbr := if ($word/@ud:Abbr)
               then local:conll-attribute($word/@ud:Abbr,"Abbr")
               else ""

              
               
let $features := replace(replace(replace(replace(
                               string-join(($abbr,$case,$definite,$degree,$foreign,$gender,$number,$person,$prontype,$reflex,$tense,$verbform),"|"),
                               "\|+","|"),
                               "^\|$","_"),
                               "^\|",""),
                               "\|$","")

let $quotes := $word/ancestor::node/descendant::node[@word=("'", '"')]/@begin

(: currently not used, but done in postprocessing by add_spaceafter.py:)
let $space_after := 
   if ($word/@end = 
   	     $word/ancestor::node/descendant::node[@word= (";",".",":","?","!",",",")","»")]/@begin)
               then "SpaceAfter=No"
               else if ($word/@word = ( "(" , "«" ) ) 
                    then "SpaceAfter=No"
                    else  if ($word/@word = ("'", '"')  and index-of($quotes,$word/@begin) mod 2 = 1 ) 
                          then "SpaceAfter=No"
                          else if ( $word/@end = 
   	                               $word/ancestor::node/descendant::node[@word= ("'",'"') and 
   	                                          index-of($quotes,@begin) mod 2 = 0]/@begin )
                                then "SpaceAfter=No"
                          else "_"

let $orig_postag := replace(replace(replace(replace($word/@postag,',','|'), '\(\)',''),'\(','|') ,'\)','')

order by number($word/@end)
return 
('&#10;',
string-join(($word/@end, $word/@word , $word/@root , $word/@ud:pos, $orig_postag, $features, $word/@ud:HeadPosition, $word/@ud:Relation,"_","_"), "	" )
)
}; 


declare function local:sanity_check($node as element(node)) as element(node) {
let $count := count($node//node[@ud:Relation="root"])
let $zeroheadpos := count($node//node[@ud:HeadPosition="0"])
let $headpositionisself := count($node//node[@ud:HeadPosition=@end])
return
 element {name($node)} { ( $node/@*, 
                             attribute {"ud:roots"} {$count}, 
                             attribute {"ud:zeroheadpos"} {$zeroheadpos},
                             attribute {"ud:headpositionisself"} {$headpositionisself},
                             for $child in $node/node return $child ) }
};

for $doc in collection($DIR) (: "/home/aardvark/corp/nl/SONAR_ccl/WRPPG_3?select=*.xml" :)
    for $article in $doc//article.published
        for $node in $article//p/alpino_ds/node (: /body/body.content/body.p/ :)
      return
      if ($MODE eq 'conll') 
      then  <pre>
            <code sentence-id="{document-uri($doc)}">
            <author-last>{$article//namelast/text()}</author-last>
            <author-first>{$article//namefirst/text()}</author-first>
            <section>{lower-case($article//section/text())}</section>
            <subsection>{lower-case($article//subsection/text())}</subsection>
            <edition>{lower-case($article//edition/text())}</edition>
            <date>{substring($article//story.date/text(),1,10)}</date>
            {$node/../sentence,
            local:conll(local:add_dependency_relations(local:add_features(local:add_pos_tags($node))))}
            !
            </code>
            </pre>
      else  <alpino_ds sentence-id="{document-uri($doc)}">
            <author-last>{$article//namelast/text()}</author-last>
            <author-first>{$article//namefirst/text()}</author-first>
            <section>{lower-case($article//section/text())}</section>
            <subsection>{lower-case($article//subsection/text())}</subsection>
            <edition>{lower-case($article//edition/text())}</edition>
            <date>{substring($article//story.date/text(),1,10)}</date>
            {$node/../sentence,
            local:sanity_check(local:add_dependency_relations(local:add_features(local:add_pos_tags($node))))
            }
            </alpino_ds>
  
