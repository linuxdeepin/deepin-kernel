#!/usr/bin/ocamlrun /usr/bin/ocaml

(* Command line arguments parsing *)
let basedir = ref "debian/arch"
let arch = ref ""
let subarch = ref ""
let flavour = ref ""
let config_name = ref ""
let verbose = ref false
let archindir = ref false

type action = Single | Create | Check
let action = ref Create

let set_action a () = action := a

let spec = [
  "-b", Arg.Set_string basedir, "base dir of the arch configurations [default: debian/arch]";
  "-ba", Arg.Set archindir, "basedir includes arch";
  "-a", Arg.Set_string arch, "arch";
  "-s", Arg.Set_string subarch, "subarch";
  "-f", Arg.Set_string flavour, "flavour";
  "-v", Arg.Set verbose, "verbose";
  "-c", Arg.Unit (set_action Check), "check";
]
let usage =
  "Check single config file : ./kconfig.ml config_file\n" ^
  "Create config file       : ./kconfig.ml [ -ba ] [ -b basedir ] -a arch [ -s subarch ] -f flavour" ^ "\n" ^
  "Check all config files   : ./kconfig.ml -c [ -b basedir ] -a arch [ -s subarch ] -f flavour" ^ "\n"

let () = Arg.parse
  spec
  (function s -> config_name := s; action := Single) 
  usage

let usage () = Arg.usage spec usage

(* Config file parsing *)
type options =
  | Config_Yes of string
  | Config_No of string
  | Config_Module of string
  | Config_Value of string * string
  | Config_Comment of string
  | Config_Empty

let print_option = function
  | Config_Yes s -> Printf.printf "CONFIG_%s=y\n" s
  | Config_No s -> Printf.printf "# CONFIG_%s is not set\n" s
  | Config_Module s -> Printf.printf "CONFIG_%s=m\n" s
  | Config_Value (s,v) -> Printf.printf "CONFIG_%s=%s\n" s v
  | Config_Comment s -> Printf.printf "#%s\n" s
  | Config_Empty -> Printf.printf "\n"
  
exception Comment
exception Error
  
let parse_config_line fd =
  let line = input_line fd in
  let len = String.length line in
  if len = 0 then Config_Empty else
  try
    if len <= 9 then raise Comment else 
    match line.[0], line.[1], line.[2], line.[3], line.[4], line.[5], line.[6], line.[7], line.[8] with 
    | '#', ' ', 'C', 'O', 'N', 'F', 'I', 'G', '_' ->
      begin
        try
          let space = String.index_from line 8 ' ' in
	  if String.sub line (space + 1) 10 = "is not set" then 
	    let o = String.sub line 9 (space - 9) in
	    Config_No o
	  else raise Comment
        with Not_found | Invalid_argument "String.sub" -> raise Comment
      end
    | '#', _, _, _, _, _, _, _, _ -> raise Comment
    | 'C', 'O', 'N', 'F', 'I', 'G', _, _, _ ->
      begin
        try
          let equal = String.index_from line 6 '=' in
	  let o = String.sub line 7 (equal - 7) in
	  let v = String.sub line (equal + 1) (len - equal - 1) in
	  match v with
	  | "y" -> Config_Yes o
	  | "m" -> Config_Module o
	  | _ -> Config_Value (o,v)
        with Not_found | Invalid_argument "String.sub" -> raise Comment
      end
    | _ -> raise Comment
  with Comment -> Config_Comment (String.sub line 1 (len - 1))

module C = Map.Make (String)

(* Map.add behavior ensures the latest entry is the one staying *)
let rec parse_config fd m =
  try 
    let line = parse_config_line fd in
    match line with
    | Config_Comment _ | Config_Empty -> parse_config fd m
    | Config_Yes s | Config_No s | Config_Module s | Config_Value (s,_) ->
      parse_config fd (C.add s line m)
  with End_of_file -> m

let print_config m = C.iter (function _ -> print_option) m

let parse_config_file name m force =
  try 
    let config = open_in name in
    let m = parse_config config m in
    close_in config;
    m
  with Sys_error s ->
    if force then raise (Sys_error s) else m

(* Defines parsing *)
type define =
  | Defines_Base of string
  | Defines_Field of string * string
  | Defines_List of string
  | Defines_Comment of string
  | Defines_Error of string
  | Defines_Empty

let print_define = function
  | Defines_Base s -> Printf.printf "[%s]\n" s
  | Defines_Field (n, v) -> Printf.printf "%s:%s\n" n v
  | Defines_List s -> Printf.printf " %s\n" s
  | Defines_Comment s -> Printf.printf "#%s\n" s
  | Defines_Error s -> Printf.printf "*** ERROR *** %s\n" s
  | Defines_Empty -> Printf.printf "\n"

let parse_define_line fd =
  let line = input_line fd in
  let len = String.length line in
  if len = 0 then begin Defines_Empty end else
  try
    match line.[0] with
    | '#' -> Defines_Comment (String.sub line 1 (len - 1))
    | '[' -> begin
        try 
          let c = String.index_from line 1 ']' in
	  Defines_Base (String.sub line 1 (c - 1))
        with Not_found | Invalid_argument "String.sub" -> raise Error
      end
    | ' ' -> Defines_List (String.sub line 1 (len - 1))
    | _ ->  begin
        try 
          let c = String.index_from line 1 ':' in
	  Defines_Field (String.sub line 0 c, String.sub line (c + 1) (len - c - 1))
        with Not_found | Invalid_argument "String.sub" -> raise Error
      end
  with Error -> Defines_Error line

let rec parse_defines fd m l =
  try 
    let line = parse_define_line fd in
    match line with
    | Defines_Comment _ | Defines_Empty -> parse_defines fd (line::m) (l+1)
    | Defines_Error error ->
      Printf.eprintf "*** Error at line %d : %s\n" l error;
      parse_defines fd m (l+1)
    | Defines_Base _ | Defines_Field _ | Defines_List _ -> parse_defines fd (line::m) (l+1)
  with End_of_file -> List.rev m

let parse_defines_file name m force =
  try 
    let defines = open_in name in
    let m = parse_defines defines m 0 in
    close_in defines;
    m
  with Sys_error s ->
    if force then raise (Sys_error s) else m

let print_defines m = List.iter print_define m

(* Main functionality *)
let get_archdir () = if !archindir then Filename.dirname !basedir else !basedir

let do_single () = 
  try
    begin if !verbose then Printf.eprintf "Reading config file %s" !config_name end;
    let config = open_in !config_name in
    let m = parse_config config C.empty in
    print_config m;
    close_in config
  with Sys_error s -> Printf.eprintf "Error: %s\n" s

let do_create () =
  if !arch <> "" && !flavour <> "" then
    try
      begin if !verbose then 
        Printf.eprintf "Creating config file for arch %s, subarch %s, flavour %s (basedir is %s)\n" !arch !subarch !flavour !basedir
      end;
      let dir = get_archdir () in
      let m = parse_config_file (dir ^ "/config") C.empty false in
      let archdir = dir ^ "/" ^ !arch in
      let m = parse_config_file (archdir ^ "/config") m false in
      let m, archdir = 
        if !subarch <> ""  && !subarch <> "none" then 
          let archdir = archdir ^ "/" ^ !subarch in
          parse_config_file (archdir ^ "/config") m false, archdir
        else m, archdir
      in
      let m = parse_config_file (archdir ^ "/config." ^ !flavour) m true in
      print_config m;
    with Sys_error s -> Printf.eprintf "Error: %s\n" s
  else
    usage ()
    
let do_check () = 
  if !arch <> "" && !flavour <> "" then
    let dir = get_archdir () in
    begin if !verbose then Printf.eprintf "Checking config files in %s\n" dir end;
    try
      let m = parse_defines_file (dir ^ "/defines") [] true in
      print_defines m
    with Sys_error s -> Printf.eprintf "Error: %s\n" s
  else
    usage ()

let () =
  match !action with
  | Single -> do_single ()
  | Create -> do_create ()
  | Check -> do_check ()
