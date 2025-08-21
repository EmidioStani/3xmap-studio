import streamlit as st
import os #for file navigation
from rdflib import Graph, URIRef, Literal, Namespace, BNode
import utils
import pandas as pd
import pickle
from rdflib.namespace import split_uri
from rdflib.namespace import OWL
from rdflib.namespace import RDF, RDFS, DC, DCTERMS
import time
import re
import uuid



#____________________________________________
#PRELIMINARY
#Aesthetics
# st.markdown("""
# <div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
#             border-radius:8px; margin-bottom:16px;">
#     <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
#          style="width:32px; margin-right:12px;">
#     <div>
#         <h3 style="margin:0; font-size:1.75rem;">
#             <span style="color:#511D66; font-weight:bold; margin-right:12px;">-----</span>
#             Build Mapping
#             <span style="color:#511D66; font-weight:bold; margin-left:12px;">-----</span>
#         </h3>
#         <p style="margin:0; font-size:0.95rem; color:#555;">
#             Build your mapping by adding <b>Triple Maps</b>, <b>Subject Maps</b>, and <b>Predicate-Object Maps</b>.
#         </p>
#     </div>
# </div>
# """, unsafe_allow_html=True)
st.markdown("""
<div style="display:flex; align-items:center; background-color:#f0f0f0; padding:12px 18px;
            border-radius:8px; margin-bottom:16px;">
    <span style="font-size:1.7rem; margin-right:18px;">🏗️</span>
    <div>
        <h3 style="margin:0; font-size:1.75rem;">
            <span style="color:#511D66; font-weight:bold; margin-right:12px;">◽◽◽◽◽</span>
            Build mapping
            <span style="color:#511D66; font-weight:bold; margin-left:12px;">◽◽◽◽◽</span>
        </h3>
        <p style="margin:0; font-size:0.95rem; color:#555;">
            Build your mapping by adding <b>Triple Maps</b>, <b>Subject Maps</b>, and <b>Predicate-Object Maps</b>.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

utils.import_st_aesthetics()
st.write("")

# Namespaces
namespaces_predefined = utils.get_predefined_ns_dict()
namespaces_default = utils.get_default_ns_dict()
namespaces = namespaces_predefined | namespaces_default
RML = namespaces["rml"]
RR = namespaces["rr"]
QL = namespaces["ql"]
MAP = namespaces["map"]
CLASS = namespaces["class"]
LS = namespaces["logicalSource"]
RDF = namespaces["rdf"]
XSD = namespaces["xsd"]
RDF = namespaces["rdf"]

BASE = Namespace(utils.get_rdfolio_base_iri())


#initialise session state variables
#TAB1
if "key_ds_uploader" not in st.session_state:
    st.session_state["key_ds_uploader"] = None
if "last_added_tm_list" not in st.session_state:
    st.session_state["last_added_tm_list"] = []
if "tm_label" not in st.session_state:
    st.session_state["tm_label"] = ""
if "tm_saved_ok_flag" not in st.session_state:
    st.session_state["tm_saved_ok_flag"] = False
if "tm_deleted_ok_flag" not in st.session_state:
    st.session_state["tm_deleted_ok_flag"] = False
if "removed_tm_list" not in st.session_state:
    st.session_state["removed_tm_list"] = []


if "confirm_button" not in st.session_state:
    st.session_state["confirm_button"] = False
if "custom_ns_dict" not in st.session_state:
    st.session_state["custom_ns_dict"] = {}

if "tm_label" not in st.session_state:
    st.session_state["tm_label"] = ""
if "selected_ds" not in st.session_state:
    st.session_state["selected_ds"] = None
if "subject_id_input" not in st.session_state:
    st.session_state["subject_id_input"] = ""
if "subject_saved_ok_new" not in st.session_state:
    st.session_state["subject_saved_ok_new"] = False
if "subject_saved_ok_existing" not in st.session_state:
    st.session_state["subject_saved_ok_existing"] = False
if "tm_ordered_list" not in st.session_state:
    st.session_state["tm_ordered_list"] = []
if "smap_ordered_list" not in st.session_state:
    st.session_state["smap_ordered_list"] = []
if "deleted_triples" not in st.session_state:
    st.session_state["deleted_triples"] = []
if "tm_deleted_ok" not in st.session_state:
    st.session_state["tm_deleted_ok"] = False
if "smap_deleted_ok" not in st.session_state:
    st.session_state["smap_deleted_ok"] = False
if "smap_unassigned_ok" not in st.session_state:
    st.session_state["smap_unassigned_ok"] = False
if "cache_tm" not in st.session_state:
    st.session_state["cache_tm"] = ""
if "pom_saved_ok" not in st.session_state:
    st.session_state["pom_saved_ok"] = False
if "om_template_list" not in st.session_state:
    st.session_state["om_template_list"] = []



select_cache_tm_toggle = False
select_cache_tm_toggle_pom = False
pom_ready_flag = False

#define on_click functions
#TAB1
def save_tm_w_existing_ls():
    tm_iri = MAP[f"{tm_label}"]  # change so that is can be defined by user
    logical_source_iri =  LS[f"{selected_existing_ls}"]   # idem ns
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, tm_label)    # to display last added tm
    # add triples
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, logical_source_iri))    #bind to logical source
    # reset fields
    st.session_state["key_tm_label_input"] = ""

def save_tm_w_new_ls():   #function to save TriplesMap upon click
    tm_iri = MAP[f"{tm_label}"]
    ds_filename = ds_file.name
    if logical_source_label:
        logical_source_iri = LS[f"{logical_source_label}"]
    else:
        logical_source_iri = BNode()
    st.session_state["tm_saved_ok_flag"] = True  # for success message
    st.session_state["last_added_tm_list"].insert(0, tm_label)    # to display last added tm
    # add triples
    st.session_state["g_mapping"].add((tm_iri, RML.logicalSource, logical_source_iri))    #bind to logical source
    st.session_state["g_mapping"].add((logical_source_iri, RML.source, Literal(ds_filename)))    #bind ls to source file
    file_extension = ds_filename.rsplit(".", 1)[-1]    # bind to reference formulation
    if file_extension.lower() == "csv":
        st.session_state["g_mapping"].add((logical_source_iri, QL.referenceFormulation, QL.CSV))
    elif file_extension.lower() == "json":
        st.session_state["g_mapping"].add((logical_source_iri, QL.referenceFormulation, QL.JSONPath))
    elif file_extension.lower() == "xml":
        st.session_state["g_mapping"].add((logical_source_iri, QL.referenceFormulation, QL.XPath))
    # reset fields
    st.session_state["key_tm_label_input"] = ""
    st.session_state["key_ds_uploader"] = str(uuid.uuid4())

def delete_triplesmap():   #function to delete a TriplesMap
    st.session_state["removed_tm_list"] = []   # save the tm that have been deleted for display
    for tm in tm_to_remove_list:
        st.session_state["removed_tm_list"].append(tm)
        utils.remove_triplesmap(tm)      # remove the tm
        if tm in st.session_state["last_added_tm_list"]:
            st.session_state["last_added_tm_list"].remove(tm)       # if it is in last added list, remove
    st.session_state["tm_deleted_ok_flag"] = True
    #reset fields
    st.session_state["key_tm_to_remove_list"] = []

def delete_all_triplesmaps():   #function to delete a TriplesMap
    st.session_state["removed_tm_list"] = []    # save the tm that have been deleted for display
    for tm in utils.get_tm_dict():
        st.session_state["removed_tm_list"].append(tm)
        utils.remove_triplesmap(tm)      # remove the tm
        if tm in st.session_state["last_added_tm_list"]:
            st.session_state["last_added_tm_list"].remove(tm)       # if it is in last added list, remove
    st.session_state["tm_deleted_ok_flag"] = True
    #reset fields
    st.session_state["key_tm_to_remove_list"] = []





def reset_input():    #function to reset input upon click
    st.session_state["overwrite_checkbox"] = False
    st.session_state["save_g_filename_flag"] = ""

def delete_labelled_subject_map():   #function to delete a Subject Map
    st.session_state["g_mapping"].remove((sm_to_remove, None, None))
    st.session_state["g_mapping"].remove((None, None, sm_to_remove))
    st.session_state["sm_to_remove"] = "Select a TriplesMap"
    st.session_state["smap_deleted_ok"] = True
    st.session_state["unassign_sm_uncollapse"] = False
    st.session_state["delete_labelled_sm_uncollapse"] = False

def unassign_subject_map():
    if len(other_tm_with_sm) != 1:       #just unassign sm to tm
        st.session_state["g_mapping"].remove((tm_to_unassign_sm_iri, RR.subjectm, None))
        st.session_state["smap_unassigned_ok"] = True
    else:       #completely remove sm
        st.session_state["g_mapping"].remove((sm_to_unassign, None, None))
        st.session_state["g_mapping"].remove((None, None, sm_to_unassign))
        st.session_state["smap_deleted_ok"] = True
    st.session_state["tm_to_unassign_sm"] = "Select a TriplesMap"
    st.session_state["unassign_sm_uncollapse"] = False
    st.session_state["delete_labelled_sm_uncollapse"] = False

def save_subject_existing():
    st.session_state["g_mapping"].add((tm_iri_existing, RR.subjectm, selected_existing_sm_iri))
    st.session_state["subject_saved_ok_existing"] = True
    st.session_state["smap_ordered_list"].insert(0, tm_iri_existing)
    st.session_state["existing_sm_uncollapse"] = False
    st.session_state["new_sm_uncollapse"] = False


def save_subject_template():   #function to save subject (template option)
    utils.update_dictionaries()
    if not s_label:
        smap_iri = BNode()
    else:
        smap_iri = MAP[s_label]

    st.session_state["g_mapping"].add((tm_iri, RR.subjectm, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RR.template, Literal(f"http://example.org/resource/{{{st.session_state["subject_id_input"]}}}")))
    st.session_state["subject_id"] = "Select a column of the data source:"
    st.session_state["subject_id_input"] = ""
    st.session_state["subject_saved_ok_new"] = True
    st.session_state["subject_label"] = ""
    st.session_state["smap_ordered_list"].insert(0, tm_iri)
    st.session_state["existing_sm_uncollapse"] = False
    st.session_state["new_sm_uncollapse"] = False


def save_subject_constant():   #function to save subject (template option)
    utils.update_dictionaries()
    if not s_label:
        smap_iri = BNode()
    else:
        smap_iri = MAP[s_label]

    st.session_state["g_mapping"].add((tm_iri, RR.subjectm, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RR.constant, Literal(f"http://example.org/resource/{st.session_state["subject_constant_input"]}")))
    st.session_state["subject_constant"] = ""
    st.session_state["subject_saved_ok_new"] = True
    st.session_state["subject_label"] = ""
    st.session_state["smap_ordered_list"].insert(0, tm_iri)
    st.session_state["existing_sm_uncollapse"] = False
    st.session_state["new_sm_uncollapse"] = False


def save_subject_reference():   #function to save subject (template option)
    utils.update_dictionaries()
    if not s_label:
        smap_iri = BNode()
    else:
        smap_iri = MAP[s_label]

    st.session_state["g_mapping"].add((tm_iri, RR.subjectm, smap_iri))
    st.session_state["g_mapping"].add((smap_iri, RML.reference, Literal(st.session_state["subject_id_input"])))
    st.session_state["subject_id"] = "Select a column of the data source:"
    st.session_state["subject_id_input"] = ""
    st.session_state["subject_saved_ok_new"] = True
    st.session_state["subject_label"] = ""
    st.session_state["smap_ordered_list"].insert(0, tm_iri)
    st.session_state["existing_sm_uncollapse"] = False
    st.session_state["new_sm_uncollapse"] = False

def save_simple_subject_class():
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["class"], subject_class))

def save_union_class():
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["class"], selected_union_class_BNode))
    st.session_state["selected_union_class_label"] = "Select a union class"

def save_external_subject_class():
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["class"], subject_class))

def delete_subject_class():
    st.session_state["g_mapping"].remove((selected_subject_bnode, RR["class"], None))

def change_to_BNode():
    st.session_state["g_mapping"].remove((selected_subject_bnode, RR["termType"], RR.IRI))
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["termType"], RR.BlankNode))

def change_to_IRI():
    st.session_state["g_mapping"].remove((selected_subject_bnode, RR["termType"], RR.BlankNode))
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["termType"], RR.IRI))

def save_subject_graph():
    st.session_state["g_mapping"].add((selected_subject_bnode, RR["graph"], subject_graph))

def delete_subject_graph():
    st.session_state["g_mapping"].remove((selected_subject_bnode, RR["graph"], None))

def save_pom_reference():
    st.session_state["g_mapping"].add((tm_iri, RR.predicateObjectm, pom_iri))
    st.session_state["g_mapping"].add((pom_iri, RR.predicate, selected_predicate_iri))
    st.session_state["g_mapping"].add((pom_iri, RR.objectm, om_iri))
    st.session_state["g_mapping"].add((om_iri, RR.column, Literal(om_column_name)))
    #term type__________________________________
    if om_term_type == "📘 Literal":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.Literal))
    elif om_term_type == "🌐 IRI":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.IRI))
    elif om_term_type == "👻 BNode":
        st.session_state["g_mapping"].add((om_iri, RR.termType, RR.BlankNode))
    #data type__________________________________
    if om_datatype and om_datatype != "Natural language text":   #second condition unneccesary
        if om_datatype.startswith("xsd:"):
            st.session_state["g_mapping"].add((om_iri, RR.datatype, XSD.om_datatype))
        elif om_datatype.startswith("rdf:"):
            st.session_state["g_mapping"].add((om_iri, RR.datatype, RDF.om_datatype))
    #language tag_____________________________________
    if om_language_tag:   #can only be given if om_datatype == "Natural language text"
        st.session_state["g_mapping"].add((om_iri, RR.language, Literal(om_language_tag)))
    #reset fields_____________________________________
    st.session_state["search_term"] = ""
    st.session_state["selected_predicate_temp"] = "Select a predicate"
    st.session_state["selected_predicate_textinput"] = ""
    st.session_state["pom_label"] = ""
    st.session_state["om_label"] = ""
    st.session_state["om_column_name"] = "Select a column of the data source"
    st.session_state["om_term_type"] = "📘 Literal"
    st.session_state["po_type"] = "🔢 Reference-valued"
    st.session_state["pom_saved_ok"] = True


def save_pom_constant():
    st.session_state["g_mapping"].add((tm_iri, RR.predicateObjectm, pom_iri))
    st.session_state["g_mapping"].add((pom_iri, RR.predicate, selected_predicate_iri))
    st.session_state["g_mapping"].add((pom_iri, RR.objectm, om_iri))
    st.session_state["g_mapping"].add((om_iri, RR.constant, selected_constant_iri))

    #reset fields_____________________________________
    st.session_state["search_term"] = ""
    st.session_state["selected_predicate_temp"] = "Select a predicate"
    st.session_state["selected_predicate_textinput"] = ""
    st.session_state["pom_label"] = ""
    st.session_state["om_label"] = ""
    st.session_state["om_term_type"] = "📘 Literal"
    st.session_state["po_type"] = "🔢 Reference-valued"
    st.session_state["pom_saved_ok"] = True

def save_om_template_fixed_part():
    st.session_state["om_template_list"].append(om_template_fixed_part)
    st.session_state["fixed_or_variable_part_radio"] = "📈 Add variable part"

def save_om_template_variable_part():
    st.session_state["om_template_list"].append("{" + om_template_variable_part + "}")
    st.session_state["fixed_or_variable_part_radio"] = "🔒 Add fixed part"

def reset_om_template():
    st.session_state["om_template_list"] = []

def save_pom_template():
    st.session_state["g_mapping"].add((tm_iri, RR.predicateObjectm, pom_iri))
    st.session_state["g_mapping"].add((pom_iri, RR.predicate, selected_predicate_iri))
    st.session_state["g_mapping"].add((pom_iri, RR.objectm, om_iri))
    #st.session_state["g_mapping"].add((om_iri, RR.template, URIRef(om_template)))
    #reset fields_____________________________________
    st.session_state["search_term"] = ""
    st.session_state["selected_predicate_temp"] = "Select a predicate"
    st.session_state["selected_predicate_textinput"] = ""
    st.session_state["pom_label"] = ""
    st.session_state["om_label"] = ""
    st.session_state["po_type"] = "🔢 Reference-valued"
    st.session_state["om_template_list"] = []








col1,col2 = st.columns([2,1.5])
if "g_mapping" not in st.session_state or not st.session_state["g_label"]:
    with col1:
        st.markdown(f"""
        <div style="background-color:#f8d7da; padding:1em;
                    border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
            ❗ You need to create or load a mapping. Please go to the
            <b style="color:#a94442;">Global Configuration page</b>.
        </div>
        """, unsafe_allow_html=True)
        st.stop()




#g = Graph() #create empty graph to store triples (this is the mapping we are building)
ds_folder_path = utils.get_ds_folder_path()   #path to folder with data sources HERE DELETE

#___________________________________________




#REVISION STARTS HERE
#____________________________________________________________
# PANELS OF THE PAGE (tabs)

tab1, tab2, tab3 = st.tabs(["Add TriplesMap", "Add Subject Map", "Add Predicate-Object Map"])


#________________________________________________
#ADD TRIPLESMAP
with tab1:
    st.write("")
    st.write("")

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message()

    # Display last added namespaces in dataframe (also option to show all ns)
    tm_dict = utils.get_tm_dict()

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    with col2b:
        st.write("")
        st.write("")
        rows = [{"TriplesMap": tm, "LogicalSource": utils.get_ls(tm),
                "DataSource": utils.get_ds(tm)} for tm in st.session_state["last_added_tm_list"]]
        last_added_tm_df = pd.DataFrame(rows)
        last_last_added_tm_df = last_added_tm_df.head(10)

        if st.session_state["last_added_tm_list"]:
            st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                    🔎 last added TriplesMaps
                </div>""", unsafe_allow_html=True)
            st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                    (complete list below)
                </div>""", unsafe_allow_html=True)
            st.dataframe(last_last_added_tm_df, hide_index=True)
            st.write("")


        #Option to show all TriplesMaps
        rows = [{"TriplesMap": tm, "LogicalSource": utils.get_ls(tm),
                "DataSource": utils.get_ds(tm)} for tm in reversed(list(tm_dict.keys()))]
        tm_df = pd.DataFrame(rows)

        with st.expander("🔎 Show all TriplesMaps"):
            st.write("")
            st.dataframe(tm_df, hide_index=True)



    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add New TriplesMap
            </div>""", unsafe_allow_html=True)
        st.markdown("")

    if st.session_state["tm_saved_ok_flag"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.write("")
            st.markdown(f"""<div class="custom-success">
                ✅ The TriplesMap <b style="color:#F63366;">{st.session_state["tm_label"]}</b> has been added!
            </div>""", unsafe_allow_html=True)
        st.session_state["tm_saved_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()

    with col1:
        col1a, col1b = st.columns([2,1])
    with col1a:
        tm_label = st.text_input("⌨️ Enter label for the new TriplesMap:*", key="key_tm_label_input")    #user-friendly name for the TriplesMap
        st.session_state["tm_label"] = tm_label

    tm_dict = utils.get_tm_dict()
    labelled_ls_list = []      #existing labelled logical sources
    for s, p, o in st.session_state["g_mapping"].triples((None, RML.logicalSource, None)):
        if isinstance(o, URIRef) and split_uri(o)[1] not in labelled_ls_list:
            labelled_ls_list.append(split_uri(o)[1])

    if tm_label:   #after a label has been given
        st.session_state["tm_label"] = tm_label
        if tm_label in tm_dict:   #if label is already in use
            with col1a:
                st.markdown(f"""
                <div style="background-color:#f8d7da; padding:1em;
                            border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
                    ❌ TriplesMap label <b style="color:#a94442;">{tm_label}</b> already in use: <br>
                    Please pick a different label.
                </div>
                """, unsafe_allow_html=True)
                st.write("")

        else:    #if label is valid

            if labelled_ls_list:  # if there exist labelled logical sources
                with col1a:
                    ls_options_list = ["📑 Assing existing Logical Source", "🆕 Assign new Logical Source"]
                    selected_ls_option = st.radio("", ls_options_list, label_visibility="collapsed")
                    st.write("")

            else:
                    selected_ls_option = "🆕 Assign new Logical Source"

            if selected_ls_option == "📑 Assing existing Logical Source":

                labelled_ls_list.insert(0, "Select a Logical Source")
                with col1a:
                    selected_existing_ls = st.selectbox("🖱️ Select an existing Logical Source:*", labelled_ls_list)

                if selected_existing_ls != "Select a Logical Source":
                    with col1a:
                        save_tm_button_existing_ls = st.button("Save", key="key_save_tm_w_existing_ls", on_click=save_tm_w_existing_ls)


            if selected_ls_option == "🆕 Assign new Logical Source":

                ds_allowed_formats = utils.get_ds_allowed_formats()            #data source for the TriplesMap
                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    ds_file = st.file_uploader(f"""🖱️Upload data source file*""",
                        type=ds_allowed_formats, key=st.session_state["key_ds_uploader"])
                with col1b:
                    logical_source_label = st.text_input("⌨️ Enter label for the logical source (optional):")
                    if logical_source_label in labelled_ls_list:
                        with col1b:
                            st.markdown(f"""
                                <div style="background-color:#fff3cd; padding:1em;
                                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                    ⚠️ The logical source label <b style="color:#cc9a06;">{logical_source_label}</b>
                                    is already in use. Please, pick a different label or leave blank.</div>
                            """, unsafe_allow_html=True)
                            st.write("")

                if ds_file and not logical_source_label in labelled_ls_list:
                    with col1a:
                        st.button("Save", key="key_save_tm_w_new_ls", on_click=save_tm_w_new_ls)

    # remove tm success message - show here if "Remove" purple heading is not going to be shown
    if not utils.get_tm_dict() and st.session_state["tm_deleted_ok_flag"]:  # show message here if "Remove" purple heading is going to be shown
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            formatted_deleted_tm = ", ".join(st.session_state["removed_tm_list"][:-1]) + " and " + st.session_state["removed_tm_list"][-1]
            if len(st.session_state["removed_tm_list"]) == 1:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The Triplesmap <b style="color:#F63366;">
                    {st.session_state["removed_tm_list"][0]}</b> has been succesfully deleted!  </div>
                """, unsafe_allow_html=True)
            elif len(st.session_state["removed_tm_list"]) < 7:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The Triplesmaps <b style="color:#F63366;">
                    {formatted_deleted_tm}</b> have been succesfully deleted!  </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ <b style="color:#F63366;">{len(st.session_state["removed_tm_list"])} TriplesMaps
                    </b> have been succesfully deleted!  </div>
                """, unsafe_allow_html=True)
            st.write("")
        st.session_state["tm_deleted_ok_flag"] = False
        time.sleep(st.session_state["success_display_time"])
        st.rerun()



    # PURPLE HEADING - REMOVE EXISTING TRIPLESMAP
    tm_dict = utils.get_tm_dict()
    if tm_dict:     # only show option if there are tm that can be removed
        with col1:
            st.write("________")
            st.markdown("""
            <div style="background-color:#e6e6fa; border:1px solid #511D66;
                        border-radius:5px; padding:10px; margin-bottom:8px;">
                <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                    🗑️ Remove Existing TriplesMap
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")


        if st.session_state["tm_deleted_ok_flag"]:  # show message here if "Remove" purple heading is going to be shown
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1a:
                formatted_deleted_tm = ", ".join(st.session_state["removed_tm_list"][:-1]) + " and " + st.session_state["removed_tm_list"][-1]
                if len(st.session_state["removed_tm_list"]) == 1:
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ The Triplesmap <b style="color:#F63366;">
                        {st.session_state["removed_tm_list"][0]}</b> has been succesfully deleted!  </div>
                    """, unsafe_allow_html=True)
                elif len(st.session_state["removed_tm_list"]) < 7:
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ The Triplesmaps <b style="color:#F63366;">
                        {formatted_deleted_tm}</b> have been succesfully deleted!  </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color:#d4edda; padding:1em;
                    border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                        ✅ <b style="color:#F63366;">{len(st.session_state["removed_tm_list"])} TriplesMaps
                        </b> have been succesfully deleted!  </div>
                    """, unsafe_allow_html=True)
                st.write("")
            st.session_state["tm_deleted_ok_flag"] = False
            time.sleep(st.session_state["success_display_time"])
            st.rerun()

        with col1:
            col1a, col1b = st.columns([2,1])

        tm_list = list(tm_dict)
        if len(tm_list) > 1:
            tm_list.insert(0, "Remove all")

        with col1a:
            tm_to_remove_list = st.multiselect("🖱️ Select TriplesMap/s:*", tm_list, key="key_tm_to_remove_list")

        if tm_to_remove_list:
            if "Remove all" not in tm_to_remove_list:
                with col1a:
                    delete_triplesmap_checkbox = st.checkbox(
                    ":gray-badge[⚠️ I am sure I want to delete the TriplesMap/s]",
                    key="delete_triplesmap_checkbox")
                if delete_triplesmap_checkbox:
                    with col1:
                        col1a, col1b = st.columns([1,2])
                    with col1a:
                        st.button("Delete", on_click=delete_triplesmap)
            else:   #if "Remove all" selected
                with col1a:
                    st.markdown(f"""<div class="custom-warning-small">
                            ⚠️ If you continue, <b>all TriplesMaps will be deleted</b>.
                            Make sure you want to go ahead.
                        </div>""", unsafe_allow_html=True)
                    st.write("")
                    delete_triplesmap_checkbox = st.checkbox(
                    ":gray-badge[⚠️ I am sure I want to delete all TriplesMaps]",
                    key="delete_triplesmap_checkbox")
                if delete_triplesmap_checkbox:
                    with col1:
                        col1a, col1b = st.columns([1,2])
                    with col1a:
                        st.button("Delete", on_click=delete_all_triplesmaps)


        with col1a:
            if st.session_state["deleted_triples"] and st.toggle("🔎 Display last removed triples") and not st.session_state["tm_deleted_ok"]:
                st.markdown(
                    """
                    <div style='background-color:#f0f0f0; padding:8px; border-radius:4px;'>
                        <b> Last deleted triples:</b>
                    </div>""", unsafe_allow_html=True)
                for s, p, o in st.session_state["deleted_triples"]:
                    if isinstance(s, URIRef):
                        s = split_uri(s)[1]
                    elif isinstance(s, BNode):
                        s = ("BNode: " + str(s)[:5] + "...")
                    if isinstance(p, URIRef):
                        p = split_uri(p)[1]
                    if isinstance(o, URIRef):
                        o = split_uri(o)[1]
                    elif isinstance(o, BNode):
                        o = ("BNode: " + str(o)[:5] + "...")
                    st.markdown(
                        f"""
                        <div style='background-color:#f0f0f0; padding:6px 10px; border-radius:5px;'>
                            <small>🔹 {s} → {p} → {o}</small>
                        </div>""", unsafe_allow_html=True)


#________________________________________________



#________________________________________________
#ADD SUBJECT MAP TO MAP
with tab2:

    st.write("")
    st.write("")

    col1,col2 = st.columns([2,1.5])

    with col2:
        col2a,col2b = st.columns([1,2])
    with col2b:
        utils.get_corner_status_message()

    # Display last added namespaces in dataframe (also option to show all ns)
    tm_dict = utils.get_tm_dict()

    with col2:
        col2a, col2b = st.columns([0.5, 2])

    with col2b:
        st.write("")
        st.write("")
        rows = [{"TriplesMap": tm, "LogicalSource": utils.get_ls(tm),
                "DataSource": utils.get_ds(tm)} for tm in st.session_state["last_added_tm_list"]]
        last_added_tm_df = pd.DataFrame(rows)
        last_last_added_tm_df = last_added_tm_df.head(10)

        if st.session_state["last_added_tm_list"]:
            st.markdown("""<div style='text-align: right; font-size: 14px; color: grey;'>
                    🔎 last added TriplesMaps
                </div>""", unsafe_allow_html=True)
            st.markdown("""<div style='text-align: right; font-size: 11px; color: grey; margin-top: -5px;'>
                    (complete list below)
                </div>""", unsafe_allow_html=True)
            st.dataframe(last_last_added_tm_df, hide_index=True)
            st.write("")


        #Option to show all TriplesMaps
        rows = [{"TriplesMap": tm, "LogicalSource": utils.get_ls(tm),
                "DataSource": utils.get_ds(tm)} for tm in reversed(list(tm_dict.keys()))]
        tm_df = pd.DataFrame(rows)

        with st.expander("🔎 Show all TriplesMaps"):
            st.write("")
            st.dataframe(tm_df, hide_index=True)



    #PURPLE HEADING - ADD NEW TRIPLESMAP
    with col1:
        st.markdown("""<div class="purple-heading">
                🧱 Add New Subject Map
            </div>""", unsafe_allow_html=True)
        st.markdown("")

        col1a, col1b = st.columns([2,1])

    st.session_state["tm_dict"] = utils.get_tm_dict() #HERE DELETE

    #SELECT THE TRIPLESMAP TO WHICH THE SUBJECT MAP WILL BE ADDED___________________________
    #only triplesmaps without subjects can be selected
    if st.session_state["cache_tm"]:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1b:
            select_cache_tm_toggle = st.toggle("", value=True)
        if select_cache_tm_toggle:
            with col1a:
                st.markdown(f"""
                    <div style="background-color:#edf7ef; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                         📍 Select last added TriplesMap: <b>{st.session_state["cache_tm"]}</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            with col1a:
                st.markdown(f"""
                    <div style="background-color:#f5f5f5; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                         📍 Select last added TriplesMap: <b>{st.session_state["cache_tm"]}</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

    with col1a:
        st.write("")

    tm_list = list(st.session_state["tm_dict"].values())
    tm_without_subject_list = []          #list of all TriplesMap which do not have a subject yet
    for tm_label, tm_iri in st.session_state["tm_dict"].items():
        if not next(st.session_state["g_mapping"].objects(tm_iri, RR.subjectm), None):   #if there is no subject for that TriplesMap
            tm_without_subject_list.append(tm_label)
    tm_without_subject_list.insert(0, "Select a TriplesMap")


    if not st.session_state["tm_dict"]:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ No TriplesMaps in mapping {st.session_state["g_label"]}.<br>
                You can add new TriplesMaps in the <b style="color:#cc9a06;">Add TriplesMap option</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

    elif len(tm_without_subject_list) == 1:
        with col1a:
            st.markdown(
                f"""
                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                🔒 <b>All existing TriplesMaps have already been assigned a subject map.</b><br>
                <ul style="margin-top:0.5em; margin-bottom:0; font-size:0.9em; list-style-type: disc; padding-left: 1.2em;">
                    <li>Note that only one subject can be assigned to each TriplesMap.</li>
                    <li>You can add new TriplesMaps in the <b style="color:#007bff;">Add TriplesMap option</b>.</li>
                </ul>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")


    else:
        #IF THERE ARE TRIPLESMAPS AVAILABLE UNCOLLAPSE OPTIONS___________________________

        #first create dictionary of all the existing Subject Maps
        existing_subject_map_dict = {"Select a Subject Map": "Select a Subject Map"}
        for sm in st.session_state["g_mapping"].objects(predicate=RR.subjectm):
            if isinstance(sm, URIRef):
                existing_subject_map_dict[split_uri(sm)[1]] = sm
        existing_subject_map_list = list(existing_subject_map_dict.keys())

        if st.session_state["cache_tm"]:
            if select_cache_tm_toggle:
                tm_label_input = st.session_state["cache_tm"]
            else:
                with col1a:
                    tm_label_input = st.selectbox("or select another TriplesMap", tm_without_subject_list, key="s_tm_label_input")
        else:
            with col1a:
                tm_label_input = st.selectbox("Select a TriplesMap", tm_without_subject_list, key="s_tm_label_input")

        tm_label_input_existing = tm_label_input
        tm_label_input_new = tm_label_input

        if tm_label_input != "Select a TriplesMap":


            with col1:
                st.markdown("""<div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>""", unsafe_allow_html=True)

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                existing_sm_uncollapse = st.toggle("", key="existing_sm_uncollapse")
            with col1a:
                st.write("")
                st.markdown("""<span style="font-size:1.1em; font-weight:bold;">📑 Select existing Subject Map</span><br>
                        <small>Select an already created Subject Map from list</small>""",
                    unsafe_allow_html=True)

            if existing_sm_uncollapse:
                with col1a:
                    if len(existing_subject_map_dict) == 1:
                        st.markdown(f"""
                            <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                ⚠️ This option is not available. No labelled Subject Maps exist in mapping {st.session_state["g_label"]}.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        tm_label_input_existing = "Select a TriplesMap"
                    else:

                        if tm_label_input_existing == "Select a TriplesMap":
                            pass
                            # with col1b:
                            #     st.write("")
                            #     st.write("")
                            #     st.markdown(f"""
                            #     <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                            #             <span style="font-size:0.95rem;">
                            #             ⚠️ You must select a TriplesMap to continue.
                            #             </span>
                            #         </div>
                            #         """, unsafe_allow_html=True)
                        else:
                            selected_existing_sm_label = st.selectbox("Choose an existing Subject Map", existing_subject_map_list)
                            selected_existing_sm_iri = existing_subject_map_dict[selected_existing_sm_label]
                            if selected_existing_sm_label != "Select a Subject Map":
                                tm_iri_existing = st.session_state["tm_dict"][tm_label_input_existing]
                                save_existing_subject_map = st.button("Save", on_click=save_subject_existing)



            with col1a:
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                    )

            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                new_sm_uncollapse = st.toggle("", key="new_sm_uncollapse")
            with col1a:
                st.write("")
                st.markdown(
                    """
                        <span style="font-size:1.1em; font-weight:bold;">🆕 Create new Subject Map</span><br>
                        <small>Create Subject Map defining its subject generation rule</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                    )
                    #REUSE: ⚙️ Define the subject generation rule. Determine the logic for subject creation based on mapping type.

            if new_sm_uncollapse:

                #GET DATA SOURCE OF THE TRIPLESMAP____________________________
                if tm_label_input_new == "Select a TriplesMap":
                    tm_iri = None
                    tm_logical_source_iri = None
                    s_generation_type = ""
                    # with col1b:
                    #     st.write("")
                    #     st.write("")
                    #     st.markdown(f"""
                    #     <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                    #             <span style="font-size:0.95rem;">
                    #             ⚠️ You must select a TriplesMap to continue.
                    #             </span>
                    #         </div>
                    #         """, unsafe_allow_html=True)

                else:   #TriplesMap selected
                    tm_iri = st.session_state["tm_dict"][tm_label_input_new]
                    tm_logical_source_iri = next(st.session_state["g_mapping"].objects(tm_iri, RML.logicalSource), None)

                    #here we get the columns of the data source for the template option
                    data_source = next(st.session_state["g_mapping"].objects(tm_logical_source_iri, RML.source), None)   #name of ds file
                    if data_source:
                        data_source_file = os.path.join(os.getcwd(), "data_sources", data_source)    #full path of ds file
                        columns_df = pd.read_csv(data_source_file)
                        column_list = columns_df.columns.tolist()
                    else:
                        column_list = []


                    with col1a:
                        s_label = st.text_input("Enter Subject Map label (optional)", key="subject_label")

                    if s_label in existing_subject_map_dict:
                        with col1a:
                            st.markdown(f"""
                                <div style="background-color:#fff3cd; padding:1em;
                                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                    ⚠️ The Subject Map label <b style="color:#cc9a06;">{s_label}</b>
                                    is already in use and will be ignored. Please, pick a different label.</div>
                            """, unsafe_allow_html=True)
                        s_label = ""   #ignore subject map label if it already exists


                    with col1:
                        col1a, col1b = st.columns([2,1])

                    with col1a:

                        s_generation_type_list = ["Template 📐", "Constant 🔒", "Reference 🔗"]

                        st.write("")
                        s_generation_type = st.radio(
                            label="Define the subject generation rule:",
                            options=s_generation_type_list,
                            horizontal=True,
                            )




                #TEMPLATE OPTION______________________________
                if s_generation_type == "Template 📐":

                    with col1b:
                        st.write("")
                        st.write("")
                        st.write("")
                        st.markdown(f"""
                            <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                    <b> 📐 Template use case </b>: <br>Dynamically construct the subject IRI using data values.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

                    #Select the column of the data source for the template
                    column_list.insert(0, "Select a column of the data source:")
                    with col1a:
                        subject_id = st.selectbox("Select the subject id", column_list, key="subject_id")

                    if subject_id != "Select a column of the data source:":
                        st.session_state["subject_id_input"] = subject_id

                    with col1a:
                        if tm_label_input_new != "Select a TriplesMap" and subject_id != "Select a column of the data source:":
                            st.button("Save subject", on_click=save_subject_template)


                #CONSTANT OPTION______________________________
                if s_generation_type == "Constant 🔒":

                    with col1b:
                        st.write("")
                        st.write("")
                        st.write("")
                        st.markdown(f"""
                            <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                    <b> 🔒 Constant use case </b>: <br>Every subject is the same fixed IRI.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

                    with col1a:
                        subject_constant = st.text_input("Enter the subject constant", key="subject_constant")

                    if subject_constant != "Enter the subject constant":
                        st.session_state["subject_constant_input"] = subject_constant

                    with col1a:
                        if tm_label_input_new != "Select a TriplesMap" and subject_constant:
                            st.button("Save subject", on_click=save_subject_constant)


                #REFERENCE OPTION______________________________
                if s_generation_type == "Reference 🔗":

                    with col1b:
                        st.write("")
                        st.write("")
                        st.write("")
                        st.markdown(f"""
                            <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                    <b> 🔗 Reference use case </b>: <br> Directly use the data value as the subject,
                                    especially for literals or when you want full control.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

                    #Select the column of the data source for the reference
                    column_list.insert(0, "Select a column of the data source:")
                    with col1a:
                        subject_id = st.selectbox("Select the subject id", column_list, key="subject_id")

                    if subject_id != "Select a column of the data source:":
                        st.session_state["subject_id_input"] = subject_id

                    with col1a:
                        if tm_label_input_new != "Select a TriplesMap" and subject_id != "Select a column of the data source:":
                            st.button("Save subject", on_click=save_subject_reference)


        if st.session_state["subject_saved_ok_existing"]:
            with col1b:
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The Subject Map has been assigned to the TriplesMap
                    <b style="color:#0f5132;">{split_uri(st.session_state["smap_ordered_list"][0])[1]}</b>.</div>
                """, unsafe_allow_html=True)
            st.session_state["subject_saved_ok_existing"] = False
            time.sleep(2)
            st.rerun()


    if st.session_state["subject_saved_ok_new"]:
        with col1:
            col1a, col1b = st.columns([1,2])
        with col1a:
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ The Subject Map has been assigned to the TriplesMap
                <b style="color:#0f5132;">{split_uri(st.session_state["smap_ordered_list"][0])[1]}</b>.</div>
            """, unsafe_allow_html=True)
        st.session_state["subject_saved_ok_new"] = False
        time.sleep(2)
        st.rerun()


    # st.write("This is for debugging purposes and will be deleted")
    # st.write("g_label: ", st.session_state["g_label"])
    #
    # st.write(f"Graph has {len(st.session_state["g_mapping"])} triples")
    # for s, p, o in list(st.session_state["g_mapping"])[:9]:  # show first 5 triples
    #     st.write(f"{s} -- {p} --> {o}")

#_________________________________________________________________


#_____________________________________________________________________
#ADD EXTRA TRIPLES TO SUBJECT MAP

    with col1:
        st.write("______________")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                ➕ Subject Map Configuration
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")


    #SELECT THE TRIPLESMAP (this will give the subject if it exists)__________________________________
    #list of all triplesmaps with assigned Subject Map
    tm_with_sm_list = ["Select a TriplesMap"]
    for tm_label, tm_iri in st.session_state["tm_dict"].items():
        if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectm, None))):
            tm_with_sm_list.append(tm_label)

    labelled_sm_list = ["Select a Subject Map"]
    for tm_label, tm_iri in st.session_state["tm_dict"].items():
        sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RR.subjectm)
        if isinstance(sm_iri, URIRef) and sm_iri not in labelled_sm_list:
            if split_uri(sm_iri)[1] not in labelled_sm_list:
                labelled_sm_list.append(split_uri(sm_iri)[1])


    with col1:
        col1a, col1b = st.columns([2,1])

    if not st.session_state["tm_dict"]:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ No TriplesMaps in mapping {st.session_state["g_label"]}.<br>
                You can add new TriplesMaps in the <b style="color:#cc9a06;">Add TriplesMap option</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

    elif len(tm_with_sm_list) == 1:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ This option is not available because no TriplesMaps have already been assigned a Subject Map yet.
                Please do so in the <b style="color:#cc9a06;">🧱 Add New Subject Map</b> section of this pannel.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

    else:

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            selected_tm_label = st.selectbox("Select a TriplesMap", tm_with_sm_list)   #select a triplesmap

        selected_sm_label = "Select a Subject Map"
        if selected_tm_label == "Select a TriplesMap":
            with col1a:
                selected_sm_label = st.selectbox("or select a labelled Subject Map", labelled_sm_list)

        if selected_sm_label != "Select a Subject Map":
            selected_sm_iri = MAP[selected_sm_label]
            selected_tm = next((s for s, p, o in st.session_state["g_mapping"].triples((None, RR.subjectm, selected_sm_iri))), None)
            selected_tm_label = split_uri(selected_tm)[1]


        if selected_tm_label == "Select a TriplesMap":
            pass
            # with col1b:
            #     st.markdown(f"""
            #         <div style="background-color:#fff9db; border:1px dashed #511D66;
            #         padding:10px; border-radius:5px; margin-bottom:8px;">
            #             <span style="font-size:0.95rem;">
            #             ⚠️ You must select a TriplesMap to continue.
            #             </span>
            #         </div>
            #         """, unsafe_allow_html=True)
        else:

            selected_tm = st.session_state["tm_dict"][selected_tm_label]        #selected tm iri
            selected_subject_bnode = st.session_state["g_mapping"].value(selected_tm, RR.subjectm)     #subject of selected tm (BNode)
            selected_subject_id = st.session_state["subject_dict"][selected_tm_label][1]
            selected_subject_type = st.session_state["subject_dict"][selected_tm_label][2]


            if selected_sm_label == "Select a Subject Map":
                if isinstance(selected_subject_bnode, URIRef):
                    with col1a:
                        st.markdown(f"""
                            <div style="background-color:#edf7ef; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                 🔖 The Subject Map assigned to the TriplesMap <b>{selected_tm_label}</b>
                                 is <b>{split_uri(selected_subject_bnode)[1]}</b>.
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        st.write("")
                elif isinstance(selected_subject_bnode, BNode):
                    with col1a:
                        st.markdown(f"""
                            <div style="background-color:#edf7ef; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                <span style="font-size:0.95rem;">
                                 🔖 The Subject Map assigned to the TriplesMap <b>{selected_tm_label}</b>
                                 is <b>_:{str(selected_subject_bnode)[:7] + "..."}</b>
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        st.write("")
            else:
                tm_assigned_to_sm_list = []
                for tm_label in st.session_state["subject_dict"]:
                    if selected_sm_label == st.session_state["subject_dict"][tm_label][3]:
                        tm_assigned_to_sm_list.append(tm_label)
                assigned_str = ", ".join(str(item) for item in tm_assigned_to_sm_list)
                with col1a:
                    st.markdown(f"""
                        <div style="background-color:#edf7ef; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                            <span style="font-size:0.95rem;">
                             🔖 The Subject Map <b>{selected_sm_label}</b> is assigned to these TriplesMaps: <b>{assigned_str}</b>.
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                    st.write("")



            #TERM TYPE - IRI by default, but can be changed to BNode
            with col1:
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                term_type_uncollapse = st.toggle("", key="term_type_uncollapse")
            with col1a:
                st.markdown(
                    """
                        <span style="font-size:1.1em; font-weight:bold;">🆔 Term type</span><br>
                        <small>Indicates the target graph for the subject map triples. If not given, the default graph will be used.</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if term_type_uncollapse:
                if not st.session_state["g_mapping"].value(selected_subject_bnode, RR["termType"]):   #If termType not indicated yet, make it IRI (default)
                    st.session_state["g_mapping"].add((selected_subject_bnode, RR["termType"], RR.IRI))
                selected_subject_term_type = st.session_state["g_mapping"].value(selected_subject_bnode, RR["termType"])

                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    if selected_subject_bnode:
                        st.write("")
                        if split_uri(selected_subject_term_type)[1] == "IRI":
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject term type:
                                    <b style="color:#007bff;">IRI</b><br>
                                    <small>Click button to change to BNode.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            with col1:
                                col1a, col1b = st.columns([1,2])
                            with col1a:
                                st.write("")
                                st.button("Change to BNode", on_click=change_to_BNode)
                        else:
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject term type:
                                    <b style="color:#007bff;">BNode</b><br>
                                    <small>Click button to change to IRI.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            with col1:
                                col1a, col1b = st.columns([1,2])
                            with col1a:
                                st.write("")
                                st.button("Change to IRI", on_click=change_to_IRI)




            #SUBJECT CLASS (ontology-based)
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                st.write("")
                st.write("")
                subject_class_uncollapse = st.toggle("", key="subject_class_uncollapse")
            with col1a:
                st.write("")
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col1a:
                st.markdown(
                    """
                        <span style="font-size:1.1em; font-weight:bold;">🏷️ Subject class</span><br>
                        <small>Declares the ontology-based class of the generated subjects.</small>
                    """,
                    unsafe_allow_html=True
                )

            if subject_class_uncollapse:

                #Check whether the subject map already has a class
                subject_class = st.session_state["g_mapping"].value(selected_subject_bnode, RR["class"])

                with col1a:
                    if subject_class and selected_subject_bnode:   #subject class already exists
                        if isinstance(subject_class, URIRef):
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject class:
                                    <b style="color:#007bff;">{split_uri(subject_class)[1]}</b><br>
                                    <small>Delete it to assign a different subject class.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        elif isinstance(subject_class, BNode) and utils.is_union_class(subject_class):
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject class:
                                    <b style="color:#007bff;">Union class {utils.get_union_class_label(subject_class)}</b><br>
                                    <small>Delete it to assign a different subject class.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        elif isinstance(subject_class, BNode):
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔒 Subject class:
                                    <b style="color:#007bff;">BNode</b><br> ({subject_class})<br>
                                    <small>Delete it to assign a different subject class.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        st.write("")
                        with col1a:
                            delete_subject_class_checkbox = st.checkbox(
                            ":gray-badge[⚠️ I am completely sure I want to delete the subject class]",
                            key="delete_subject_class")
                        if delete_subject_class_checkbox:
                            with col1:
                                col1a, col1b = st.columns([1,2])
                            with col1a:
                                st.button("Delete", on_click=delete_subject_class)


                    elif selected_subject_bnode:        #subject class does not exist
                        with col1a:
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔓 Subject class:
                                    <b style="color:#007bff;">not given</b><br>
                                    <small>Enter below.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        st.write("")

                        #WE ORGANISE THE ONTOLOGY CLASSES IN DIFFERENT DICTIONARIES
                        #dictionary for simple classes
                        ontology_classes_dict = {"Select a class": ""}
                        class_triples = set()
                        class_triples |= set(st.session_state["g_ontology"].triples((None, RDF.type, OWL.Class)))   #collect owl:Class definitions
                        class_triples |= set(st.session_state["g_ontology"].triples((None, RDF.type, RDFS.Class)))    # collect rdfs:Class definitions
                        for s, p, o in class_triples:   #we add to dictionary removing the BNodes
                            if not isinstance(s, BNode):
                                ontology_classes_dict[split_uri(s)[1]] = s

                        #dictionary for superclasses
                        superclass_dict = {"Select a superclass": ""}
                        classes_in_superclass_dict = {"Select a class": ""}
                        for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, None)))):
                            if not isinstance(o, BNode) and o not in superclass_dict.values():
                                superclass_dict[o.split("/")[-1].split("#")[-1]] = o


                        #ONLY SHOW OPTIONS IF THE ONTOLOGY HAS THEM
                        class_type_option_list = ["Class outside ontology"]
                        if len(ontology_classes_dict) != 1:   #if the ontology includes at least one class
                            class_type_option_list.insert(0, "Ontology class")


                        if class_type_option_list == ["Class outside ontology"]:   #no ontology or no classes in ontology
                            class_type = "Class outside ontology"
                        else:    #there is an ontology and it has classes
                            with col1a:
                                class_type = st.radio(
                                    label="Select an option:",
                                    options=class_type_option_list,
                                    horizontal=True,
                                    label_visibility="collapsed"
                                )


                        #ONTOLOGY CLASS
                        if class_type == "Ontology class":

                            if len(superclass_dict) != 1:   #there exists at least one superclass (show option to select a superclass)
                                with col1a:
                                    superclass = st.selectbox("Select a superclass to filter classes (optional)", list(superclass_dict.keys()))   #superclass label
                                classes_in_superclass_dict[superclass] = superclass_dict[superclass]
                            else:     #no superclasses exist (don't give option to select superclass)
                                superclass = "Select a superclass"

                            if superclass != "Select a superclass":   #a superclass has been selected
                                superclass = superclass_dict[superclass] #we get the superclass iri
                                for s, p, o in list(set(st.session_state["g_ontology"].triples((None, RDFS.subClassOf, superclass)))):
                                    classes_in_superclass_dict[split_uri(s)[1]] = s
                                with col1a:
                                    subject_class = st.selectbox("Select a class", list(classes_in_superclass_dict.keys()))   #class label
                                subject_class = classes_in_superclass_dict[subject_class] #we get the superclass iri
                            else:  #no superclass selected or no superclasses exist, give all classes as options
                                with col1a:
                                    subject_class = st.selectbox("Select a class", list(ontology_classes_dict.keys()), key="subject_class_from_all")   #class label
                                subject_class = ontology_classes_dict[subject_class] #we get the superclass iri


                            if subject_class != "":
                                with col1:
                                    col1a,col2a = st.columns([1,2])
                                with col1a:
                                    st.button("Save", key="save_subject_class", on_click=save_simple_subject_class)



                        #CLASS OUTSIDE ONTOLOGY
                        if class_type == "Class outside ontology":
                            with col1b:
                                st.markdown("<br><br>", unsafe_allow_html=True)
                            if st.session_state["g_ontology"] and len(class_type_option_list) == 1: #there is an ontology but it has no classes
                                with col1b:
                                    st.write("")
                                    st.markdown(f"""
                                        <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                            <span style="font-size:0.95rem;">
                                              🚧<b> Caution</b>: The ontology {st.session_state["g_ontology_components_dict"]}
                                              does not define any classes. <b>Classes can only be added manually</b>.
                                              Using an ontology with predefined classes is recommended.
                                            </span>
                                        </div>
                                        """, unsafe_allow_html=True)
                            elif st.session_state["g_ontology"]:   #there exists an ontology and it has classes
                                with col1b:
                                    st.write("")
                                    st.markdown(f"""
                                        <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                            <span style="font-size:0.95rem;">
                                              🚧<b> Caution</b>: The option \"Class outside ontology\"
                                              <b>lacks ontology alignment</b> and could result in structural inconsistencies.
                                              We recommend an ontology-driven approach.
                                            </span>
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                with col1b:
                                    st.markdown(f"""
                                        <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                                            <span style="font-size:0.95rem;">
                                              🚧<b> Caution</b>: You are working without an ontology. We recommend loading an ontology
                                               from the <b> Global Configuration</b> panel.
                                            </span>
                                        </div>
                                        """, unsafe_allow_html=True)

                            subject_class_prefix_list = list(st.session_state["ns_dict"].keys())
                            with col1a:
                                subject_class_prefix_list.insert(0,"Select a namespace")
                            with col1a:
                                subject_class_prefix = st.selectbox("Select a namespace", subject_class_prefix_list)
                            if len(subject_class_prefix_list) == 1:
                                with col1b:
                                    st.write("")
                                    st.markdown(f"""
                                        <div style="background-color:#f8d7da; border:1px dashed #a94442; padding:10px; border-radius:5px; margin-bottom:8px;">
                                            <span style="font-size:0.95rem;">
                                              ⚠️ No namespaces available. You can add namespaces in the
                                               <b>Global Configuration</b> page.
                                            </span>
                                        </div>
                                        """, unsafe_allow_html=True)
                            if subject_class_prefix != "Select a namespace":
                                NS = Namespace(st.session_state["ns_dict"][subject_class_prefix])
                            with col1a:
                                subject_class_input = st.text_input("Enter subject class")
                            if subject_class_input and subject_class_prefix != "Select a namespace":
                                subject_class = NS[subject_class_input]
                                with col1a:
                                    st.button("Save", on_click=save_external_subject_class)


            #GRAPH - If not given, default graph    HERE condider if rr:graphMap option (dynamic) is worth it
            with col1a:
                st.write("")
                st.markdown(
                    """
                    <div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                graph_map_uncollapse = st.toggle("", key="graph_map_uncollapse")
            with col1a:
                st.markdown(
                    """
                        <span style="font-size:1.1em; font-weight:bold;">🗺️️ Graph map</span><br>
                        <small>Indicates the target graph for the subject map triples. If not given, the default graph will be used.</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.write("")

            if graph_map_uncollapse:
                subject_graph = st.session_state["g_mapping"].value(selected_subject_bnode, RR["graph"])

                with col1:
                    col1a, col1b = st.columns([2,1])
                with col1a:
                    if subject_graph and selected_subject_bnode:    #subject graph already given
                        st.markdown(
                            f"""
                            <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                🔒 Subject graph:
                                <b style="color:#007bff;">{split_uri(subject_graph)[1]}</b><br>
                                <small>Delete it to assign a different subject graph.</small>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.write("")

                        with col1a:
                            delete_subject_graph_checkbox = st.checkbox(
                            ":gray-badge[⚠️ I am completely sure I want to delete the subject graph]",
                            key="delete_subject_graph")
                        if delete_subject_graph_checkbox:
                            with col1:
                                col1a, col1b = st.columns([1,2])
                            with col1a:
                                st.button("Delete", on_click=delete_subject_graph)

                    elif selected_subject_bnode:       #subject graph not given
                        with col1a:
                            st.markdown(
                                f"""
                                <div style="background-color:#f9f9f9; padding:1em; border-radius:5px; color:#333333; border:1px solid #e0e0e0;">
                                    🔓 Subject graph:
                                    <b style="color:#007bff;">not given</b><br>
                                    <small>Enter below.</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        st.write("")
                        subject_graph_input = st.text_input("Enter subject graph", key="subject_graph_input")
                        subject_graph = BASE[subject_graph_input]
                        with col1:
                            col1a, col1b = st.columns([1,2])
                        with col1a:
                            if subject_graph_input:
                                st.button("Save", on_click=save_subject_graph)


    with col1:
        st.write("---")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🗑️ Remove existing Subject Map
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

    tm_with_sm_list = ["Select a TriplesMap"]
    for tm_label, tm_iri in st.session_state["tm_dict"].items():
        if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectm, None))):
            tm_with_sm_list.append(tm_label)

    with col1:
        col1a, col1b = st.columns([2,1])

    if not st.session_state["tm_dict"]:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ No TriplesMaps in mapping {st.session_state["g_label"]}.<br>
                You can add new TriplesMaps in the <b style="color:#cc9a06;">Add TriplesMap option</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

    elif len(tm_with_sm_list) == 1:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ This option is not available because no TriplesMaps have already been assigned a Subject Map yet.
                Please do so in the <b style="color:#cc9a06;">🧱 Add New Subject Map</b> section of this pannel.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

    else:

        with col1:
            col1a, col1b = st.columns([2,1])

        with col1:
            st.markdown("""<div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                </div>""", unsafe_allow_html=True)

        with col1:
            col1a, col1b = st.columns([2,1])
        with col1b:
            delete_labelled_sm_uncollapse = st.toggle("", key="delete_labelled_sm_uncollapse")
        with col1a:
            st.write("")
            st.markdown("""<span style="font-size:1.1em; font-weight:bold;">🔖 Delete labelled Subject Map</span><br>
                    <small>Select a labelled Subject Map and erase it completely</small>""",
                unsafe_allow_html=True)

        if delete_labelled_sm_uncollapse:
            with col1:
                col1a, col1b = st.columns([2,1])

            utils.update_dictionaries()
            sm_to_remove_list = ["Select a Subject Map"]
            for tm_label in st.session_state["subject_dict"]:
                if st.session_state["subject_dict"][tm_label][3] not in sm_to_remove_list and not isinstance(st.session_state["subject_dict"][tm_label][3], str):
                    sm_to_remove_list.append(st.session_state["subject_dict"][tm_label][3])

            if len(sm_to_remove_list) == 1:
                with col1a:
                    st.markdown(f"""
                    <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                            <span style="font-size:0.95rem;">
                            ⚠️ There are no labelled Subject Maps to remove.
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
            else:

                with col1a:
                    sm_to_remove_label = st.selectbox("Select a Subject Map", sm_to_remove_list, key="sm_to_remove")
                    sm_to_remove = MAP[sm_to_remove_label]

                if sm_to_remove_label != "Select a Subject Map":
                    assigned_tm_list = []
                    for tm_label in st.session_state["subject_dict"]:
                        if sm_to_remove_label == st.session_state["subject_dict"][tm_label][3]:
                            assigned_tm_list.append(tm_label)
                    with col1a:
                        assigned_str = ", ".join(str(item) for item in assigned_tm_list)
                        st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:1em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                ⚠️ The Subject Map <b style="color:#cc9a06;">{sm_to_remove_label}</b>
                                is currently assigned to these TriplesMaps: <b style="color:#cc9a06;">{assigned_str}</b>.
                                </div>
                        """, unsafe_allow_html=True)
                        st.write("")
                        delete_labelled_subject_map_checkbox = st.checkbox(
                        ":gray-badge[⚠️ I am completely sure I want to delete the Subject Map]",
                        key="delete_labelled_subject_map_checkbox")
                    if delete_labelled_subject_map_checkbox:
                        with col1:
                            col1a, col1b = st.columns([1,2])
                        with col1a:
                            st.button("Delete", on_click=delete_labelled_subject_map)

        with col1a:
            st.markdown("""<div style="border-top:3px dashed #b5b5d0; padding-top:12px;">
                </div>""", unsafe_allow_html=True)
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1b:
            unassign_sm_uncollapse = st.toggle("", key="unassign_sm_uncollapse")
        with col1a:
            st.write("")
            st.markdown("""<span style="font-size:1.1em; font-weight:bold;">
            🎯 Unassign Subject Map of a TriplesMap</span><br>
                    <small>Select a TriplesMap and unassign its Subject Map</small>""",
                unsafe_allow_html=True)

        if unassign_sm_uncollapse:
            with col1:
                col1a, col1b = st.columns([2,1])

            tm_with_sm_list = ["Select a TriplesMap"]
            for tm_label, tm_iri in st.session_state["tm_dict"].items():
                if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectm, None))):
                    tm_with_sm_list.append(tm_label)

            if len(tm_with_sm_list) == 1:
                with col1a:
                    st.write("")
                    st.markdown(f"""
                    <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                            <span style="font-size:0.95rem;">
                            ⚠️ There are no TriplesMap with assigned Subject Maps.
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

            else:

                with col1a:
                    tm_to_unassign_sm = st.selectbox("Select a TriplesMap", tm_with_sm_list, key="tm_to_unassign_sm")

                if tm_to_unassign_sm != "Select a TriplesMap":
                    tm_to_unassign_sm_iri = st.session_state["tm_dict"][tm_to_unassign_sm]
                    sm_to_unassign = st.session_state["g_mapping"].value(subject=tm_to_unassign_sm_iri, predicate=RR.subjectm)
                    other_tm_with_sm = [s for s, p, o in st.session_state["g_mapping"].triples((None, RR.subjectm, sm_to_unassign))]

                    st.write("HERE2", other_tm_with_sm)
                    if isinstance(sm_to_unassign, URIRef):
                        sm_to_unassign_label = split_uri(sm_to_unassign)[1]
                    elif isinstance(sm_to_unassign, BNode):
                        sm_to_unassign_label = "BNode: " + str(sm_to_unassign)[:5] + "..."

                    if len(other_tm_with_sm) != 1:
                        with col1a:
                            st.markdown(f"""
                                <div style="background-color:#fff3cd; padding:1em;
                                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                    ⚠️ The TriplesMap <b style="color:#cc9a06;">{tm_to_unassign_sm}</b>
                                    has been assigned the Subject Map <b style="color:#cc9a06;">{sm_to_unassign_label}</b>.
                                    </div>
                            """, unsafe_allow_html=True)
                            st.write("")

                    else:
                        with col1a:
                            st.markdown(f"""
                                <div style="background-color:#fff3cd; padding:1em;
                                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                    ⚠️ The TriplesMap <b style="color:#cc9a06;">{tm_to_unassign_sm}</b>
                                    has been assigned the Subject Map <b style="color:#cc9a06;">{sm_to_unassign_label}</b>.<br>
                                    <br>
                                    The Subject Map <b style="color:#cc9a06;">{sm_to_unassign_label}</b> is not assigned
                                    to any other TriplesMap, so it will be <b style="color:#cc9a06;">completely removed<b> if you unnasign it
                                    (all triples related to it will be erased).
                                    </div>
                            """, unsafe_allow_html=True)
                            st.write("")



                    with col1a:
                        unassign_sm_checkbox = st.checkbox(
                        ":gray-badge[⚠️ I am completely sure I want to unassign the Subject Map]",
                        key=" unassign_sm_checkbox")
                    if unassign_sm_checkbox:
                        with col1:
                            col1a, col1b = st.columns([1,2])
                        with col1a:
                            st.button("Unassign", on_click=unassign_subject_map)



        if st.session_state["smap_deleted_ok"]:
            with col1b:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The <b style="color:#007bff;">Subject Map
                    </b> has been succesfully deleted!  </div>
                """, unsafe_allow_html=True)
                st.write("")
            st.session_state["smap_deleted_ok"] = False
            time.sleep(2)
            st.rerun()

        if st.session_state["smap_unassigned_ok"]:
            with col1b:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ The <b style="color:#007bff;">Subject Map
                    </b> has been succesfully unassigned!  </div>
                """, unsafe_allow_html=True)
                st.write("")
            st.session_state["smap_unassigned_ok"] = False
            st.session_state["smap_deleted_ok"] = False
            time.sleep(2)
            st.rerun()


    with col1:
        st.write("---")
        st.markdown("""
        <div style="background-color:#e6e6fa; border:1px solid #511D66;
                    border-radius:5px; padding:10px; margin-bottom:8px;">
            <div style="font-size:1.1rem; font-weight:600; color:#511D66;">
                🔎 Subject Map Snapshot
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")


    #SHOW COMPLETE INFORMATION ON THE SUBJECT MAPS___________________________________
    utils.update_dictionaries()
    subject_df_complete = utils.build_complete_subject_df()
    filtered_tm_without_subject_list = [item for item in tm_without_subject_list if item != "Select a TriplesMap"]
    tm_without_subject_df = pd.DataFrame(filtered_tm_without_subject_list, columns=['TriplesMap without Subject Map'])

    with col1:
        with st.expander("ℹ️ Show all Subject Maps"):
            st.write("")
            st.write("")
            if not subject_df.empty:
                st.dataframe(subject_df.drop(columns="TriplesMap IRI").copy(), hide_index=True)
            else:
                st.write("⚠️ No Subject Maps have been assigned yet!")

    with col1:
        with st.expander("ℹ️ Show all Subject Map entries"):
            st.write("")
            st.write("")
            if not subject_df_complete.empty:
                st.dataframe(subject_df_complete, hide_index=True)
            else:
                st.write("⚠️ No Subject Maps have been assigned yet!")

    with col1:
        with st.expander("ℹ️ Show all TriplesMap with no Subject Map"):
            st.write("")
            st.write("")
            if not tm_without_subject_df.empty:
                st.dataframe(tm_without_subject_df, hide_index=True)
            else:
                st.write("✔️ All TriplesMap have already been assigned Subject Maps!")

#________________________________________________

#________________________________________________
#ADD PREDICATE-OBJECT MAP TO MAP
with tab3:

    col1,col2, col3 = st.columns([2,0.2,0.8])


    with col3:
        st.markdown(f"""
            <div style="background-color:#e6e6fa; padding:1em; border-radius:5px;
            color:#2a0134; border:1px solid #511D66;">
                <img src="https://img.icons8.com/ios-filled/50/000000/flow-chart.png" alt="mapping icon"
                style="vertical-align:middle; margin-right:8px; height:20px;">
                You are currently working with mapping
                <b style="color:#007bff;">{st.session_state["g_label"]}</b>.
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.session_state["g_ontology_components_dict"]:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
                        border-radius:5px; color:#155724; border:1px solid #444;">
                🧩 The ontology
                <b style="color:#007bff;">{st.session_state["g_ontology_components_dict"]}</b>
                is currently loaded.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background-color:#fff9db; padding:10px; border-radius:5px; margin-bottom:8px; border:1px solid #ccc;">
                    <span style="font-size:0.95rem; color:#333;">
                        🚫 <b>No ontology</b> is loaded.<br>
                    </span>
                    <span style="font-size:0.82rem; color:#555;">
                        Working without an ontology could result in structural inconsistencies and
                        is <b>especially discouraged when building Predicate-Object Maps</b>.
                    </span>
                </div>
            """, unsafe_allow_html=True)


    #POM_____________________________________________________
    tm_label = ""
    selected_predicate = ""

    with col1:
        col1a, col1b = st.columns([2,1])

    with col1a:
        st.markdown(
            """
                <span style="font-size:1.1em; font-weight:bold;">🆕 Create the Predicate-Object Map</span><br>
                <small>Create the Predicate-Object Map.</small>
            """,
            unsafe_allow_html=True
        )


    #list of all triplesmaps with assigned Subject Map
    tm_with_sm_list = ["Select a TriplesMap"]
    for tm_label, tm_iri in st.session_state["tm_dict"].items():
        if any(st.session_state["g_mapping"].triples((tm_iri, RR.subjectm, None))):
            tm_with_sm_list.append(tm_label)

    if not st.session_state["tm_dict"]:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ No TriplesMaps in mapping {st.session_state["g_label"]}.<br>
                You can add new TriplesMaps in the <b style="color:#cc9a06;">Add TriplesMap option</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")
            st.stop()

    elif len(tm_with_sm_list) == 1:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff9db; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                ⚠️ The existing TriplesMaps have not been assigned a Subject Map.
                You can add new TriplesMaps in the <b style="color:#007bff;">Add TriplesMap option</b>
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")
            st.stop()


    if st.session_state["cache_tm"] and next(st.session_state["g_mapping"].objects(st.session_state["tm_dict"][st.session_state["cache_tm"]], RR.subjectm), None):
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1b:
            select_cache_tm_toggle_pom = st.toggle("", value=True)
        if select_cache_tm_toggle_pom:
            with col1a:
                st.markdown(f"""
                    <div style="background-color:#edf7ef; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                         📍 Select last added TriplesMap: <b>{st.session_state["cache_tm"]}</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("")
        else:
            with col1a:
                st.markdown(f"""
                    <div style="background-color:#f5f5f5; border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                         📍 Select last added TriplesMap: <b>{st.session_state["cache_tm"]}</b>.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("")

    if select_cache_tm_toggle_pom:   #get the cache tm
        tm_label = st.session_state["cache_tm"]
    else:                    #or get the tm from a selectbox
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            tm_label_temp = st.selectbox("🖱️ Select a Triples map*", tm_with_sm_list)
            tm_label = tm_label_temp if tm_label_temp != tm_with_sm_list[0] else ""


    if tm_label:
        tm_iri = st.session_state["tm_dict"][tm_label]
        sm_iri = st.session_state["g_mapping"].value(subject=tm_iri, predicate=RR.subjectm)

        if st.session_state["g_ontology_components_dict"]:
            ontology_predicates_list = []
            ontology_predicates_dict = {}
            for xtuple in st.session_state["g_ontology"].triples((None, RDF.type ,None)):
                try:
                    pred = split_uri(xtuple[0])[1]
                    ontology_predicates_dict[split_uri(xtuple[0])[1]] = xtuple[0]
                    if pred not in ontology_predicates_list:
                        ontology_predicates_list.append(pred)
                except:
                    pass
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                search_term = st.text_input("💬 Type to filter predicates", key="search_term")
            filtered_options = [s for s in ontology_predicates_list if search_term.lower() in str(s).lower()]
            filtered_options.insert(0, "Select a predicate")
            with col1a:
                selected_predicate_temp = st.selectbox("🖱️ Select a predicate*", filtered_options, key="selected_predicate_temp")
                selected_predicate = selected_predicate_temp if selected_predicate_temp != filtered_options[0] else ""
                selected_predicate_iri = ontology_predicates_dict[selected_predicate] if selected_predicate else ""
        else:
            ns_prefix_list = list(st.session_state["ns_dict"].keys())
            ns_prefix_list.insert(0, "Select a namespace")
            with col1:
                col1a, col1b = st.columns([2,1])
            with col1b:
                selected_predicate_ns_temp = st.selectbox("Select a namespace for the predicate*", ns_prefix_list)
                selected_predicate_ns = selected_predicate_ns_temp if not selected_predicate_ns_temp == ns_prefix_list[0] else ""
                if len(ns_prefix_list) == 1:
                    st.write("")
                    with col1:
                        st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:1em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                ⚠️ No custom namespaces have been added. Please do so in
                                the <b style="color:#cc9a06;">Global Configuration</b> page to continue.
                                </div>
                        """, unsafe_allow_html=True)

            with col1a:
                selected_predicate = st.text_input("⌨️ Enter a predicate*", key="selected_predicate_textinput")
            if selected_predicate and selected_predicate_ns:
                selected_predicate_iri = URIRef(st.session_state["ns_dict"][selected_predicate_ns] + selected_predicate)
            else:
                selected_predicate = ""

    if not tm_label:
        with col1b:
            st.markdown(f"""
                <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                    <span style="font-size:0.95rem;">
                        ℹ️ Only TriplesMaps with an assigned Subject Map are shown.
                        You can assign a Subject Map to a Triples Map in the Add Subject Map section.
                    </span>
                </div>
                """, unsafe_allow_html=True)

    else:
        with col1:
            st.write("")
            col1a, col1b = st.columns([1,1])
        with col1a:
            pom_label = st.text_input("🔖 Enter Predicate-Object Map label (optional)", key="pom_label")
        pom_iri = BNode() if not pom_label else MAP[pom_label]
        if next(st.session_state["g_mapping"].triples((None, RR.predicateObjectm, pom_iri)), None):
            with col1a:
                st.markdown(f"""
                    <div style="background-color:#fff3cd; padding:1em;
                    border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                        ⚠️ The Predicate-Object Map label <b style="color:#cc9a06;">{pom_label}</b>
                        is already in use and will be ignored. Please, pick a different label.</div>
                """, unsafe_allow_html=True)
            pom_label = ""

        with col1b:
            om_label = st.text_input("🔖Enter Object Map label (optional)", key="om_label")
        om_iri = BNode() if not om_label else MAP[om_label]
        if next(st.session_state["g_mapping"].triples((None, RR.objectm, om_iri)), None):
            with col1b:
                st.markdown(f"""
                    <div style="background-color:#fff3cd; padding:1em;
                    border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                        ⚠️ The Object Map label <b style="color:#cc9a06;">{om_label}</b>
                        is already in use and will be ignored. Please, pick a different label.</div>
                """, unsafe_allow_html=True)
            om_label = ""



    if tm_label:
        if isinstance(sm_iri, URIRef):
            sm_label = split_uri(sm_iri)[1]
        elif isinstance(sm_iri, BNode):
            sm_label = "_:" + str(sm_iri)[:7] + "..."
        if selected_predicate:
            pom_ready_flag = True

    if tm_label:
        tm_logical_source_iri = next(st.session_state["g_mapping"].objects(tm_iri, RML.logicalSource), None)
        data_source = next(st.session_state["g_mapping"].objects(tm_logical_source_iri, RML.source), None)
        if data_source:
            data_source_file = os.path.join(os.getcwd(), "data_sources", data_source)    #full path of ds file
            columns_df = pd.read_csv(data_source_file)
            column_list = columns_df.columns.tolist()
        else:
            column_list = []

        column_list.insert(0, "Select a column of the data source")


    st.write("______")





    col1, col2, col3 = st.columns([2,0.2, 0.8])

    with col1:
        st.markdown(
            """
                <span style="font-size:1.1em; font-weight:bold;">🏗️ Create the Object Map</span><br>
                <small>Create the Object Map.</small>
            """,
            unsafe_allow_html=True
        )


    if tm_label:
        col1, col2, col3 = st.columns([1, 0.2, 3])
        po_options = ["🔢 Reference-valued", "🔒 Constant-valued", "📐 Template-valued"]

        with col1:
            st.markdown(""" <span style="font-size:1em; font-weight:bold;">
            Predicate-Object Map type:</span><br></div>""",unsafe_allow_html=True)
            po_type = st.radio("", po_options, label_visibility="collapsed", key="po_type")

    else:
        with col1:
            col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff3cd; padding:1em;
                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                    ⚠️ You must select a TriplesMap to continue.</div>
            """, unsafe_allow_html=True)
        po_type = ""


    #_______________________________________________
    #REFERENCE-VALUED OBJECT MAP
    if po_type == "🔢 Reference-valued":
        om_datatype = ""
        om_language_tag = ""
        om_ready_flag_reference = False

        with col3:
            col3a, col3b = st.columns(2)
        with col3a:
            om_column_name_temp = st.selectbox("Select the column of the data source*", column_list, key="om_column_name")
            om_column_name = om_column_name_temp if om_column_name_temp != column_list[0] else ""

        with col3b:
            om_term_type = st.radio(label="Choose the term type*", options=["📘 Literal", "🌐 IRI", "👻 BNode"], horizontal=True, key="om_term_type")

        if om_column_name and om_term_type == "📘 Literal":
            rdf_datatypes = [
                "Select data type", "Natural language text", "xsd:string",
                "xsd:integer", "xsd:decimal", "xsd:float", "xsd:double",
                "xsd:boolean", "xsd:date", "xsd:dateTime", "xsd:time",
                "xsd:anyURI", "rdf:XMLLiteral", "rdf:HTML", "rdf:JSON"]

            with col3a:
                om_datatype_temp = st.selectbox("Select data type (optional)", rdf_datatypes)
                om_datatype = om_datatype_temp if om_datatype_temp != rdf_datatypes[0] else ""

            if om_datatype == "Natural language text":
                language_tags = [
                    "Select language tag", "en", "es", "fr", "de", "zh",
                    "ja", "pt-BR", "en-US", "ar", "ru", "hi", "zh-Hans", "sr-Cyrl"]

                with col3b:
                    om_language_tag_temp = st.selectbox("🌍 Select language tag*", language_tags)
                    om_language_tag = om_language_tag_temp if om_language_tag_temp != language_tags[0] else ""


        if om_datatype != "Natural language text":
            if om_column_name and om_term_type:
                om_ready_flag_reference = True
        else:
            if om_column_name and om_term_type and om_language_tag:
                om_ready_flag_reference = True

    #_______________________________________________
    #CONSTANT-VALUED OBJECT MAP
    if po_type == "🔒 Constant-valued":
        om_ready_flag_constant = False

        with col3:
            col3a, col3b = st.columns(2)
        with col3a:
            om_constant = st.text_input("Enter constant*", key="om_constant")

        with col3b:
            om_constant_type = st.radio(label="Choose constant type*", options=["📘 Literal", "🌐 IRI"], horizontal=True, key="om_constant_type")

        if om_constant_type == "🌐 IRI":
            ns_prefix_list = list(st.session_state["ns_dict"].keys())
            ns_prefix_list.insert(0, "Select a namespace")
            with col3a:
                selected_constant_ns_temp = st.selectbox("Select a namespace for the constant*", ns_prefix_list)
                selected_constant_ns = selected_constant_ns_temp if not selected_constant_ns_temp == ns_prefix_list[0] else ""
                if len(ns_prefix_list) == 1:
                    st.write("")
                    with col3b:
                        st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:1em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                ⚠️ No custom or ontology namespaces have been added. Please do so in
                                the <b style="color:#cc9a06;">Global Configuration</b> page to continue.
                                </div>
                        """, unsafe_allow_html=True)


        if om_constant_type == "🌐 IRI" and om_constant and selected_constant_ns:
            selected_constant_iri = URIRef(st.session_state["ns_dict"][selected_constant_ns] + om_constant)
            om_ready_flag_constant = True
        if om_constant_type == "📘 Literal" and om_constant:
            selected_constant_iri = Literal(om_constant)
            om_ready_flag_constant = True

    #_______________________________________________
    #TEMPLATE-VALUED OBJECT MAP
    if po_type == "📐 Template-valued":
        om_ready_flag_template = False

        with col3:
            col3a, col3b, col3c = st.columns([1,0.1,1])
        with col3a:
            ns_prefix_list = list(st.session_state["ns_dict"].keys())
            ns_prefix_list.insert(0, "Select a namespace")
            with col3a:
                om_template_ns_temp = st.selectbox("Select a namespace for the template*", ns_prefix_list)
                om_template_ns = om_template_ns_temp if not om_template_ns_temp == ns_prefix_list[0] else ""
                if len(ns_prefix_list) == 1:
                    st.write("")
                    with col3b:
                        st.markdown(f"""
                            <div style="background-color:#fff3cd; padding:1em;
                            border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                                ⚠️ No custom or ontology namespaces have been added. Please do so in
                                the <b style="color:#cc9a06;">Global Configuration</b> page to continue.
                                </div>
                        """, unsafe_allow_html=True)

            fixed_or_variable_part_radio = st.radio(
                label="", options=["🔒 Add fixed part", "📈 Add variable part", "🗑️ Reset template"],
                label_visibility="collapsed",
                key="fixed_or_variable_part_radio")

        with col3a:
            if fixed_or_variable_part_radio == "🔒 Add fixed part":
                om_template_fixed_part = st.text_input("Enter fixed part", key="om_fixed_part_temp")
                if re.search(r"[ \t\n\r<>\"{}|\\^`]", om_template_fixed_part):
                    st.markdown(f"""
                        <div style="background-color:#fff3cd; padding:1em;
                        border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                            ⚠️ You included a space or an unescaped character, which is discouraged.</div>
                    """, unsafe_allow_html=True)
                    st.write("")
                if om_template_fixed_part:
                    save_om_template_fixed_part_button = st.button("Add", key="save_om_template_fixed_part_button", on_click=save_om_template_fixed_part)

            elif fixed_or_variable_part_radio == "📈 Add variable part":
                om_template_variable_part_temp = st.selectbox("Select the column of the data source", column_list, key="om_template_variable_part_temp")
                om_template_variable_part = om_template_variable_part_temp if om_template_variable_part_temp != column_list[0] else ""
                if st.session_state["om_template_list"] and st.session_state["om_template_list"][-1].endswith("}"):
                    st.markdown(f"""
                        <div style="background-color:#fff3cd; padding:1em;
                        border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                            ⚠️ Including two adjacent variable parts is strongly discouraged.
                            <b>Best practice:</b> Add a separator between variables to improve clarity.</div>
                    """, unsafe_allow_html=True)
                    st.write("")
                if om_template_variable_part:
                    save_om_template_variable_part_button = st.button("Add", key="save_om_template_variable_part_button", on_click=save_om_template_variable_part)

            elif fixed_or_variable_part_radio == "🗑️ Reset template":
                st.button("Reset", on_click=reset_om_template)

        with col3c:
            om_template_base = "".join(st.session_state["om_template_list"])
            if om_template_ns:
                om_template_ns_iri = st.session_state["ns_dict"][om_template_ns]
            elif not om_template_ns and "" in st.session_state["ns_dict"]:
                om_template_ns_iri = st.session_state["ns_dict"][om_template_ns]
            else:
                om_template_ns_iri = ""
            if om_template_base:
                om_template = om_template_ns_iri + om_template_base
                st.write("")
                st.write("")
                st.markdown(f"""
                <div style="background-color:#f2f2f2; padding:10px; border-radius:5px; margin-bottom:8px;">
                    <span style="font-size:0.95rem; word-wrap:break-word; overflow-wrap:anywhere; display:block;">
                        <b> 📐 Your template so far</b>: <br>
                        {om_template}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="padding:0px; margin-bottom:8px;">
                        <span style="font-size:0.85rem; word-wrap:break-word; overflow-wrap:anywhere; display:block;">
                            🛈 You can keep adding more parts.
                        </span>
                    </div>
                """, unsafe_allow_html=True)
                if not om_template_ns:
                    if "" in st.session_state["ns_dict"]:
                        st.markdown(f"""
                            <div style="padding:0px; margin-bottom:8px;">
                                <span style="font-size:0.85rem; word-wrap:break-word; overflow-wrap:anywhere; display:block;">
                                    ⚠ You are using the default namespace provided by the ontology.
                                    To select a different option, use the dropdown menu.
                                </span>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div style="padding:0px; margin-bottom:8px;">
                                <span style="font-size:0.85rem; word-wrap:break-word; overflow-wrap:anywhere; display:block;">
                                    ⚠ You need to select a namespace.
                                </span>
                            </div>
                        """, unsafe_allow_html=True)

        if om_template_base and om_template_ns_iri:
            om_ready_flag_template = True



    st.write("______")


    col1, col2, col3 = st.columns([2, 0.2, 0.8])
    with col1:
        col1a, col1b = st.columns([2,1])
        with col1a:
            st.markdown(
                """
                    <span style="font-size:1.1em; font-weight:bold;">💾 Check and save the Predicate-Object Map</span><br>
                """,
                unsafe_allow_html=True
            )

    col1, col2, col3 = st.columns(3)

    if st.session_state["pom_saved_ok"]:
        with col1:
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:1em;
            border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                ✅ Predicate-Object Map saved correctly! </div>
            """, unsafe_allow_html=True)
        st.session_state["pom_saved_ok"] = False
        time.sleep(2)
        st.rerun()


    if pom_ready_flag:
        with col1:
            st.markdown(f"""
            <style>
            .vertical-table-green td {{padding: 4px 8px; vertical-align: top;
                font-size: 0.85rem;}}
            .vertical-table-green {{border-collapse: collapse; width: 100%;
                background-color: #edf7ef; border-radius: 5px;}}
            .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                padding-bottom: 6px;}}
            </style>

            <table class="vertical-table-green">
            <tr class="title-row"><td colspan="2">🔎 Predicate-Object Map</td></tr>
            <tr><td>🔖 <b>TriplesMap*:</b></td><td>{tm_label}</td></tr>
            <tr><td><b>Subject Map*:</b></td><td>{sm_label}</td></tr>
            <tr><td><b>Predicate*:</b></td><td>{selected_predicate}</td></tr>
            <tr><td><b>POM label:</b></td><td>{pom_label}</td></tr>
            <tr><td><b>OM label:</b></td><td>{om_label}</td></tr>
            <tr class="title-row"><td colspan="2">✔️ Required fields completed</td></tr>
            </table>
            """, unsafe_allow_html=True)
    elif tm_label:
        with col1:
            st.markdown(f"""
            <style>
            .vertical-table-yellow td {{padding: 4px 8px; vertical-align: top;
                font-size: 0.85rem;}}
            .vertical-table-yellow {{border-collapse: collapse; width: 100%;
                background-color: #fff9db; border-radius: 5px;}}
            .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                padding-bottom: 6px;}}
            </style>

            <table class="vertical-table-yellow">
            <tr class="title-row"><td colspan="2">🔎 Predicate-Object Map</td></tr>
            <tr><td>🔖 <b>TriplesMap*:</b></td><td>{tm_label}</td></tr>
            <tr><td><b>Subject Map*:</b></td><td>{sm_label}</td></tr>
            <tr><td><b>Predicate*:</b></td><td>{selected_predicate}</td></tr>
            <tr><td><b>POM label:</b></td><td>{pom_label}</td></tr>
            <tr><td><b>OM label:</b></td><td>{om_label}</td></tr>
            <tr class="title-row"><td colspan="2">⚠️ Required fields incomplete</td></tr>
            </table>
            """, unsafe_allow_html=True)
    else:
        with col1a:
            st.markdown(f"""
                <div style="background-color:#fff3cd; padding:1em;
                border-radius:5px; color:#856404; border:1px solid #ffeeba;">
                    ⚠️ You must select a TriplesMap to continue.</div>
            """, unsafe_allow_html=True)

    if po_type == "🔢 Reference-valued":

        if om_ready_flag_reference and om_datatype != "Natural language text":
            with col2:
                st.markdown(f"""
                <style>
                .vertical-table-green td {{padding: 4px 8px; vertical-align: top;
                    font-size: 0.85rem;}}
                .vertical-table-green {{border-collapse: collapse; width: 100%;
                    background-color: #edf7ef; border-radius: 5px;}}
                .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                    padding-bottom: 6px;}}
                </style>

                <table class="vertical-table-green">
                <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                <tr><td>🔖 <b>Column name*:</b></td><td>{om_column_name}</td></tr>
                <tr><td><b>Term type*:</b></td><td>{om_term_type}</td></tr>
                <tr><td><b>Data type:</b></td><td>{om_datatype}</td></tr>
                <tr class="title-row"><td colspan="2">✔️ Required fields completed</td></tr>
                </table>
                """, unsafe_allow_html=True)
        elif om_ready_flag_reference and om_datatype == "Natural language text":
            with col2:
                st.markdown(f"""
                <style>
                .vertical-table-green td {{padding: 4px 8px; vertical-align: top;
                    font-size: 0.85rem;}}
                .vertical-table-green {{border-collapse: collapse; width: 100%;
                    background-color: #edf7ef; border-radius: 5px;}}
                .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                    padding-bottom: 6px;}}
                </style>

                <table class="vertical-table-green">
                <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                <tr><td>🔖 <b>Column name*:</b></td><td>{om_column_name}</td></tr>
                <tr><td><b>Term type*:</b></td><td>{om_term_type}</td></tr>
                <tr><td><b>Data type:</b></td><td>{om_datatype}</td></tr>
                <tr><td><b>Language tag*:</b></td><td>{om_language_tag}</td></tr>
                <tr class="title-row"><td colspan="2">✔️ Required fields completed</td></tr>
                </table>
                """, unsafe_allow_html=True)
        elif not om_ready_flag_reference and om_datatype != "Natural language text":
            with col2:
                st.markdown(f"""
                <style>
                .vertical-table-yellow td {{padding: 4px 8px; vertical-align: top;
                    font-size: 0.85rem;}}
                .vertical-table-yellow {{border-collapse: collapse; width: 100%;
                    background-color: #fff9db; border-radius: 5px;}}
                .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                    padding-bottom: 6px;}}
                </style>

                <table class="vertical-table-yellow">
                <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                <tr><td>🔖 <b>Column name*:</b></td><td>{om_column_name}</td></tr>
                <tr><td><b>Term type*:</b></td><td>{om_term_type}</td></tr>
                <tr><td><b>Data type:</b></td><td>{om_datatype}</td></tr>
                <tr class="title-row"><td colspan="2">⚠️ Required fields incomplete</td></tr>
                </table>
                """, unsafe_allow_html=True)
        elif not om_ready_flag_reference and om_datatype == "Natural language text":
            with col2:
                st.markdown(f"""
                <style>
                .vertical-table-yellow td {{padding: 4px 8px; vertical-align: top;
                    font-size: 0.85rem;}}
                .vertical-table-yellow {{border-collapse: collapse; width: 100%;
                    background-color: #fff9db; border-radius: 5px;}}
                .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                    padding-bottom: 6px;}}
                </style>

                <table class="vertical-table-yellow">
                <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                <tr><td>🔖 <b>Column name*:</b></td><td>{om_column_name}</td></tr>
                <tr><td><b>Term type*:</b></td><td>{om_term_type}</td></tr>
                <tr><td><b>Data type:</b></td><td>{om_datatype}</td></tr>
                <tr><td><b>Language tag*:</b></td><td>{om_language_tag}</td></tr>
                <tr class="title-row"><td colspan="2">⚠️ Required fields incomplete</td></tr>
                </table>
                """, unsafe_allow_html=True)

        if pom_ready_flag and om_ready_flag_reference:
            with col3:
                col3a, col3b = st.columns([0.5,1.5])
            with col3b:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ All required fields are complete.<br>
                    🧐 Double-check the information before saving. </div>
                """, unsafe_allow_html=True)
                st.write("")
                save_pom_reference_button = st.button("Save", on_click=save_pom_reference)
        else:
            with col3:
                st.markdown(f"""
                    <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            ⚠️ All required fields (*) must be filled in order to save a Predicate-Object Map.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("")


    if po_type == "🔒 Constant-valued":

        if om_ready_flag_constant and om_constant_type == "📘 Literal":
            with col2:
                st.markdown(f"""
                <style>
                .vertical-table-green td {{padding: 4px 8px; vertical-align: top;
                    font-size: 0.85rem;}}
                .vertical-table-green {{border-collapse: collapse; width: 100%;
                    background-color: #edf7ef; border-radius: 5px;}}
                .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                    padding-bottom: 6px;}}
                </style>

                <table class="vertical-table-green">
                <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                <tr><td>🔖 <b>Constant*:</b></td><td>{om_constant}</td></tr>
                <tr class="title-row"><td colspan="2">✔️ Required fields completed</td></tr>
                </table>
                """, unsafe_allow_html=True)
        elif om_ready_flag_constant and om_constant_type == "🌐 IRI":
            with col2:
                st.markdown(f"""
                <style>
                .vertical-table-green td {{padding: 4px 8px; vertical-align: top;
                    font-size: 0.85rem;}}
                .vertical-table-green {{border-collapse: collapse; width: 100%;
                    background-color: #edf7ef; border-radius: 5px;}}
                .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                    padding-bottom: 6px;}}
                </style>

                <table class="vertical-table-green">
                <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                <tr><td>🔖 <b>Constant prefix*:</b></td><td>{selected_constant_ns}</td></tr>
                <tr><td>🔖 <b>Constant*:</b></td><td>{om_constant}</td></tr>
                <tr class="title-row"><td colspan="2">✔️ Required fields completed</td></tr>
                </table>
                """, unsafe_allow_html=True)
        elif not om_ready_flag_constant and om_constant_type == "📘 Literal":
            with col2:
                st.markdown(f"""
                <style>
                .vertical-table-yellow td {{padding: 4px 8px; vertical-align: top;
                    font-size: 0.85rem;}}
                .vertical-table-yellow {{border-collapse: collapse; width: 100%;
                    background-color: #fff9db; border-radius: 5px;}}
                .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                    padding-bottom: 6px;}}
                </style>

                <table class="vertical-table-yellow">
                <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                <tr><td>🔖 <b>Constant*:</b></td><td>{om_constant}</td></tr>
                <tr class="title-row"><td colspan="2">⚠️ Required fields incomplete</td></tr>
                </table>
                """, unsafe_allow_html=True)
        elif not om_ready_flag_constant and om_constant_type == "🌐 IRI":
            with col2:
                st.markdown(f"""
                <style>
                .vertical-table-yellow td {{padding: 4px 8px; vertical-align: top;
                    font-size: 0.85rem;}}
                .vertical-table-yellow {{border-collapse: collapse; width: 100%;
                    background-color: #fff9db; border-radius: 5px;}}
                .title-row td {{font-size: 0.9rem;font-weight: bold;text-align: center;
                    padding-bottom: 6px;}}
                </style>

                <table class="vertical-table-yellow">
                <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                <tr><td>🔖 <b>Constant prefix*:</b></td><td>{selected_constant_ns}</td></tr>
                <tr><td>🔖 <b>Constant*:</b></td><td>{om_constant}</td></tr>
                <tr class="title-row"><td colspan="2">⚠️ Required fields incomplete</td></tr>
                </table>
                """, unsafe_allow_html=True)

        if pom_ready_flag and om_ready_flag_constant:
            with col3:
                col3a, col3b = st.columns([0.5,1.5])
            with col3b:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ All required fields are complete.<br>
                    🧐 Double-check the information before saving. </div>
                """, unsafe_allow_html=True)
                st.write("")
                save_pom_constant_button = st.button("Save", on_click=save_pom_constant)
        else:
            with col3:
                st.markdown(f"""
                    <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            ⚠️ All required fields (*) must be filled in order to save a Predicate-Object Map.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("")

    if po_type == "📐 Template-valued":

        if om_ready_flag_template:
            with col2:
                st.markdown(f"""
                    <style>
                    .vertical-table-green td {{
                        padding: 4px 8px;
                        vertical-align: top;
                        font-size: 0.85rem;
                        word-break: break-word;
                        overflow-wrap: anywhere;
                        max-width: 100%;
                    }}
                    .vertical-table-green {{
                        border-collapse: collapse;
                        width: 100%;
                        background-color: #edf7ef;
                        border-radius: 5px;
                        table-layout: fixed;
                    }}
                    .title-row td {{
                        font-size: 0.9rem;
                        font-weight: bold;
                        text-align: center;
                        padding-bottom: 6px;
                    }}
                    </style>

                    <table class="vertical-table-green">
                        <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                        <tr>
                            <td>🔖 <b>Template namespace*:</b></td>
                            <td><span style="display:block;">{om_template_ns}</span></td>
                        </tr>
                        <tr>
                            <td>🔖 <b>Template*:</b></td>
                            <td><span style="display:block;">{om_template}</span></td>
                        </tr>
                        <tr class="title-row"><td colspan="2">⚠️ Required fields incomplete</td></tr>
                    </table>
                """, unsafe_allow_html=True)
        else:
            with col2:
                st.markdown(f"""
                    <style>
                    .vertical-table-yellow td {{
                        padding: 4px 8px;
                        vertical-align: top;
                        font-size: 0.85rem;
                        word-break: break-word;
                        overflow-wrap: anywhere;
                        max-width: 100%;
                    }}
                    .vertical-table-yellow {{
                        border-collapse: collapse;
                        width: 100%;
                        background-color: #fff9db;
                        border-radius: 5px;
                        table-layout: fixed;
                    }}
                    .title-row td {{
                        font-size: 0.9rem;
                        font-weight: bold;
                        text-align: center;
                        padding-bottom: 6px;
                    }}
                    </style>

                    <table class="vertical-table-yellow">
                        <tr class="title-row"><td colspan="2">🔎 Object Map</td></tr>
                        <tr>
                            <td>🔖 <b>Template namespace*:</b></td>
                            <td><span style="display:block;">{om_template_ns}</span></td>
                        </tr>
                        <tr>
                            <td>🔖 <b>Template*:</b></td>
                            <td><span style="display:block;">{om_template}</span></td>
                        </tr>
                        <tr class="title-row"><td colspan="2">⚠️ Required fields incomplete</td></tr>
                    </table>
                """, unsafe_allow_html=True)


        if pom_ready_flag and om_ready_flag_template:
            with col3:
                col3a, col3b = st.columns([0.5,1.5])
            with col3b:
                st.markdown(f"""
                <div style="background-color:#d4edda; padding:1em;
                border-radius:5px; color:#155724; border:1px solid #c3e6cb;">
                    ✅ All required fields are complete.<br>
                    🧐 Double-check the information before saving. </div>
                """, unsafe_allow_html=True)
                st.write("")
                save_pom_template_button = st.button("Save", on_click=save_pom_template)
        else:
            with col3:
                st.markdown(f"""
                    <div style="border:1px dashed #511D66; padding:10px; border-radius:5px; margin-bottom:8px;">
                        <span style="font-size:0.95rem;">
                            ⚠️ All required fields (*) must be filled in order to save a Predicate-Object Map.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.write("")



#________________________________________________


#________________________________________________
#SAVE PROGRESS
if st.session_state["20_option_button"] == "save_progress":

    st.markdown(f"""
    <div style="background-color:#f8d7da; padding:1em;
                border-radius:5px; color:#721c24; border:1px solid #f5c6cb;">
        ❌ This section is not ready yet.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

    col1, col2 = st.columns(2)

    save_g_folder_path = utils.get_g_folder_path()
    existing_files_list = [f for f in os.listdir(save_g_folder_path) if f.endswith(".pkl")]
    with col1:
        save_g_filename = st.text_input(
        f"Enter the filename to save the mapping {st.session_state["g_label"]} (without extension):", key="save_g_filename_flag")
        if save_g_filename and (save_g_filename + ".pkl") in existing_files_list:
            st.warning(f"""The file {save_g_filename} is already in use. Are you sure you want to
            overwrite it?""")
            overwrite_checkbox = st.checkbox(f"""I am I want to overwrite it""", key="overwrite_checkbox")
        else:
            overwrite_checkbox = True


        if overwrite_checkbox:
            if save_g_filename:
                st.session_state["save_g_filename"] = save_g_filename + ".pkl"
            confirm_button = st.button("Save progress", on_click=reset_input)


            if confirm_button:

                save_g_full_path = utils.get_g_full_path(st.session_state["save_g_filename"])

                with open(save_g_full_path, "wb") as f:
                    pickle.dump(st.session_state["g_mapping"], f)


                st.success(f"""The mapping {st.session_state["candidate_label_flag"]}
                 has been saved to file {st.session_state["save_g_filename"]}.""")



#________________________________________________







    # #OPTION TO SHOW INFORMATION_________________________
    # with col2:    #display all the TriplesMaps in a dataframe
    #     col2a,col2b = st.columns(2)
    # with col2b:
    #     st.write("")
    #     st.write("")
    #
    #     with col2:
    #         col2a,col2b = st.columns([0.1,2])
    #     with col2b:
    #         with st.expander("ℹ️ Show panel information"):
    #             st.markdown(""" <br>
    #                     💬 <b>Working with subject maps:</b>
    #                     <ul style="font-size:0.85rem; margin-left:10px; padding-left:15px; list-style-type: disc;">
    #                         <li>
    #                             First, create a TriplesMap in the <b>Add TriplesMap</b> panel.
    #                         </li>
    #                         <li>
    #                             Then, go to panel <b> Add Subject Map </b> to set the Subject Map of the TriplesMap
    #                             (each TriplesMap can only be assigned one Subject Map).
    #                         </li>
    #                         <li>
    #                             Create the Subject Map in section <b>🧱 Add New Subject Map</b>.
    #                         </li>
    #                         <li>
    #                             You can add more details in the <b>➕ Subject Map Configuration</b> section (optional):
    #                             <ul style="list-style-type: none; margin: 0; padding-left: 0;">
    #                                 <li>🏷️ <b>Subject class</b>: Declares the subject’s class (ontology-based).
    #                                 Allows to select union or intersection classes if included in the ontology.</li>
    #                                 <li>🆔 <b>Term type</b>: Specifies whether the subject is an IRI or a blank node.</li>
    #                                 <li>🗺️️ <b>Graph map</b>: Designates the named graph for storing the generated triples.</li>
    #                             </ul>
    #                         </li>
    #                     </ul>
    #                 """, unsafe_allow_html=True)
