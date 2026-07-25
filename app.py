import streamlit as st
import os
from pathlib import Path
from PIL import Image

import config
from core.pipeline import ByePIIPipeline
from reports.report_generator import ReportGenerator

try:
    favicon_image = Image.open(config.ASSETS_DIR / "circular_logo.png")
    st.set_page_config(
        page_title="byePII (demo)",
        page_icon=favicon_image,
        layout="wide"
    )
except Exception:
    st.set_page_config(
        page_title="byePII (demo)",
        page_icon=favicon_image,
        layout="wide"
    )

css_path = config.ASSETS_DIR / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = None
if "document_name" not in st.session_state:
    st.session_state.document_name = None
if "original_pages" not in st.session_state:
    st.session_state.original_pages = []
if "redacted_pages" not in st.session_state:
    st.session_state.redacted_pages = []
if "redacted_file_path" not in st.session_state:
    st.session_state.redacted_file_path = None
if "report_json_path" not in st.session_state:
    st.session_state.report_json_path = None
if "texts_json_path" not in st.session_state:
    st.session_state.texts_json_path = None

logo_path = config.ASSETS_DIR / "logo_no_bg.png"
col_logo, col_text = st.columns([2, 4], vertical_alignment="center")
with col_logo:
    if logo_path.exists():
        st.image(str(logo_path), width=400)
with col_text:
    st.markdown('<h1 class="brand-title" style="text-align: left; margin: 0; line-height: 1.1; font-size: 2.6rem;">byePII</h1>', unsafe_allow_html=True)
    st.markdown('<p class="brand-subtitle" style="text-align: left; margin: 0; margin-top: 3px; font-size: 1rem;">Enterprise Document Anonymization Platform powered by AI</p>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("#### <i class='lucide-settings'></i> Redaction Settings & Policies", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3, col_p4, col_p5, col_p6 = st.columns(6)
    with col_p1:
        c_box, c_lbl = st.columns([1, 4])
        with c_box:
            redact_names = st.checkbox("", value=True, key="names", label_visibility="collapsed", help="Redact person names, director names, shareholder names, etc.")
        with c_lbl:
            st.markdown("<span style='font-size: 1.05rem;'><i class='lucide-user'></i> Names</span>", unsafe_allow_html=True)
            
    with col_p2:
        c_box, c_lbl = st.columns([1, 4])
        with c_box:
            redact_emails = st.checkbox("", value=True, key="emails", label_visibility="collapsed", help="Redact email addresses.")
        with c_lbl:
            st.markdown("<span style='font-size: 1.05rem;'><i class='lucide-mail'></i> Emails</span>", unsafe_allow_html=True)
            
    with col_p3:
        c_box, c_lbl = st.columns([1, 4])
        with c_box:
            redact_phones = st.checkbox("", value=True, key="phones", label_visibility="collapsed", help="Redact phone and mobile numbers.")
        with c_lbl:
            st.markdown("<span style='font-size: 1.05rem;'><i class='lucide-phone'></i> Phones</span>", unsafe_allow_html=True)
            
    with col_p4:
        c_box, c_lbl = st.columns([1, 4])
        with c_box:
            redact_addresses = st.checkbox("", value=True, key="addresses", label_visibility="collapsed", help="Redact residential, mailing, office, and factory addresses.")
        with c_lbl:
            st.markdown("<span style='font-size: 1.05rem;'><i class='lucide-map-pin'></i> Addresses</span>", unsafe_allow_html=True)
            
    with col_p5:
        c_box, c_lbl = st.columns([1, 4])
        with c_box:
            redact_organizations = st.checkbox("", value=True, key="organizations", label_visibility="collapsed", help="Redact companies, organizations, banks, auditors, law firms, etc.")
        with c_lbl:
            st.markdown("<span style='font-size: 1.05rem;'><i class='lucide-building-2'></i> Orgs</span>", unsafe_allow_html=True)

    with col_p6:
        c_box, c_lbl = st.columns([1, 4])
        with c_box:
            redact_images = st.checkbox("", value=True, key="images", label_visibility="collapsed", help="Blur sensitive images (e.g. Aadhar card, PAN card, logos).")
        with c_lbl:
            st.markdown("<span style='font-size: 1.05rem;'><i class='lucide-image'></i> Images</span>", unsafe_allow_html=True)
            
    st.divider()
    
    col_opt1, col_opt2 = st.columns([3, 2])
    with col_opt1:
        c_box, c_lbl = st.columns([1, 10])
        with c_box:
            preserve_consistency = st.toggle("", value=config.PRESERVE_CONSISTENCY, label_visibility="collapsed", help="Ensures that the same real-world entity is replaced by the same synthetic entity consistently throughout the document.")
        with c_lbl:
            st.markdown("<span style='font-size: 1rem;'><i class='lucide-refresh-cw'></i> Preserve Fake Data Consistency</span>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("##### <i class='lucide-upload-cloud'></i> Upload PDF, DOCX or TXT Document to Redact", unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Upload Document",
    type=config.SUPPORTED_DOCUMENTS,
    label_visibility="collapsed"
)

if uploaded_file:
    st.session_state.document_name = uploaded_file.name
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### <i class='lucide-file-text'></i> Uploaded Document", unsafe_allow_html=True)
            st.markdown(f"**Name:** `{uploaded_file.name}`")
            st.markdown(f"**Size:** `{uploaded_file.size / 1024:.2f} KB`")
        with col2:
            st.markdown("##### <i class='lucide-shield'></i> Active Configuration", unsafe_allow_html=True)
            active_policies = []
            if redact_names: active_policies.append("Names")
            if redact_emails: active_policies.append("Emails")
            if redact_phones: active_policies.append("Phones")
            if redact_addresses: active_policies.append("Addresses")
            if redact_organizations: active_policies.append("Organizations")
            if redact_images: active_policies.append("Images")
            st.markdown(f"**Policies Active:** {', '.join(active_policies) if active_policies else 'None'}")
            st.markdown(f"**Consistency Mode:** `{'Enabled' if preserve_consistency else 'Disabled'}`")

st.markdown("<br>", unsafe_allow_html=True)
col_run1, col_run2, col_run3 = st.columns([1, 1.5, 1])
with col_run2:
    run_redaction = st.button(
        "Run Redaction Pipeline",
        use_container_width=True,
        type="primary"
    )

if run_redaction:
    if uploaded_file is None:
        st.warning("Please upload a document first.")
        st.stop()
        
    with st.spinner("Processing document through anonymization pipeline..."):
        try:
            input_file_path = config.UPLOAD_DIR / uploaded_file.name
            with open(input_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            config.PRESERVE_CONSISTENCY = preserve_consistency
            config.REDACT_IMAGES = redact_images
            
            disabled_categories = set()
            if not redact_names: disabled_categories.add("names")
            if not redact_emails: disabled_categories.add("emails")
            if not redact_phones: disabled_categories.add("phones")
            if not redact_addresses: disabled_categories.add("addresses")
            if not redact_organizations: disabled_categories.add("organizations")
            
            pipeline = ByePIIPipeline(disabled_categories=disabled_categories)
            res = pipeline.process_file(str(input_file_path))
            
            label_counts = {
                "PERSON": 0, "ORG": 0, "EMAIL": 0, "PHONE": 0, "ADDRESS": 0
            }
            for ent in res.get("entities", []):
                lbl = ent.get("label", "PERSON").upper()
                if lbl in label_counts:
                    label_counts[lbl] += 1
                else:
                    if lbl in ("COMPANY", "ORGANIZATION"):
                        label_counts["ORG"] += 1
                    elif lbl in ("EMAIL_ADDRESS", "EMAIL"):
                        label_counts["EMAIL"] += 1
                    elif lbl in ("PHONE_NUMBER", "PHONE"):
                        label_counts["PHONE"] += 1
                    elif lbl in ("ADDRESS", "LOCATION", "RESIDENTIAL_ADDRESS", "MAILING_ADDRESS", "CORPORATE_OFFICE"):
                        label_counts["ADDRESS"] += 1
                        
            report_gen = ReportGenerator(res.get("entities", []))
            report_json_path = config.OUTPUT_DIR / f"report_{input_file_path.stem}.json"
            report_gen.save_json(str(report_json_path))
            
            texts_json_path = config.OUTPUT_DIR / f"texts_report_{input_file_path.stem}.json"
            report_gen.save_texts_only_json(str(texts_json_path))
            
            st.session_state.results = label_counts
            st.session_state.original_pages = res.get("original_pages", [])
            st.session_state.redacted_pages = res.get("redacted_pages", [])
            st.session_state.redacted_file_path = res.get("redacted_file_path", None)
            st.session_state.report_json_path = str(report_json_path)
            st.session_state.texts_json_path = str(texts_json_path)
            
            st.success("Anonymization pipeline completed successfully!")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if st.session_state.results:
    st.markdown('<h3 class="section-title"><i class="lucide-bar-chart-3"></i> PII Detection Summary</h3>', unsafe_allow_html=True)
    cols = st.columns(5)
    items = list(st.session_state.results.items())
    icons = {
        "PERSON": ("user", "PERSONS"),
        "ORG": ("building-2", "ORGS"),
        "EMAIL": ("mail", "EMAILS"),
        "PHONE": ("phone", "PHONES"),
        "ADDRESS": ("map-pin", "ADDRESSES")
    }
    for index, (label, value) in enumerate(items):
        icon_name, display_label = icons.get(label, ("help-circle", label))
        with cols[index % 5]:
            st.markdown(f"""
            <div class="custom-metric-card">
                <div class="custom-metric-label"><i class="lucide-{icon_name}"></i> {display_label}</div>
                <div class="custom-metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<h3 class="section-title"><i class="lucide-download"></i> Download Processed Artifacts</h3>', unsafe_allow_html=True)
    download1, download2, download3, download4 = st.columns(4)
    red_path = st.session_state.redacted_file_path
    rep_path = st.session_state.report_json_path
    texts_path = st.session_state.texts_json_path

    is_pdf = red_path.lower().endswith(".pdf") if red_path else False
    is_docx = red_path.lower().endswith(".docx") if red_path else False
    is_txt = red_path.lower().endswith(".txt") if red_path else False

    with download1:
        if red_path and os.path.exists(red_path) and is_pdf:
            with open(red_path, "rb") as f:
                st.download_button(
                    "Download Redacted PDF",
                    data=f.read(),
                    file_name=os.path.basename(red_path),
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.download_button(
                "Download PDF",
                data=b"",
                disabled=True,
                use_container_width=True,
                help="PDF is not supported for the uploaded document type"
            )

    with download2:
        if red_path and os.path.exists(red_path) and is_docx:
            with open(red_path, "rb") as f:
                st.download_button(
                    "Download Redacted DOCX",
                    data=f.read(),
                    file_name=os.path.basename(red_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        elif red_path and os.path.exists(red_path) and is_txt:
            with open(red_path, "rb") as f:
                st.download_button(
                    "Download Redacted TXT",
                    data=f.read(),
                    file_name=os.path.basename(red_path),
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.download_button(
                "Download DOCX/TXT",
                data=b"",
                disabled=True,
                use_container_width=True
            )

    with download3:
        if rep_path and os.path.exists(rep_path):
            with open(rep_path, "rb") as f:
                st.download_button(
                    "Download Full JSON Audit Log",
                    data=f.read(),
                    file_name=os.path.basename(rep_path),
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.download_button(
                "Download Report",
                data=b"",
                disabled=True,
                use_container_width=True
            )

    with download4:
        if texts_path and os.path.exists(texts_path):
            with open(texts_path, "rb") as f:
                st.download_button(
                    "Download Texts-Only JSON",
                    data=f.read(),
                    file_name=os.path.basename(texts_path),
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.download_button(
                "Download Texts JSON",
                data=b"",
                disabled=True,
                use_container_width=True
            )

banner_path = Path("assets/banner.png")
if banner_path.exists():
    import base64
    with open(banner_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(f"""
    <div style="text-align: center; margin-top: 50px; margin-bottom: 20px;">
        <img src="data:image/png;base64,{img_b64}" style="width: 100%; max-width: 100%; border-radius: 12px;"/>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; margin-bottom: 20px;">
        <img src="assets/banner.png" style="width: 100%; max-width: 100%; border-radius: 12px;"/>
    </div>
    """, unsafe_allow_html=True)
