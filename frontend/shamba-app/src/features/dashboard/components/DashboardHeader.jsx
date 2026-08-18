import farmer from '../../../assets/farmer.png'

function DashboardHeader() {
    return (
        <section className="welcome-banner">
            <div className="header-card">
                <div className="header-content">
                    <span className="badge">AI Ag-Tech Platform</span>
                    <h1>Muraho! Ikaze kuri <span className="highlight">ShambaGuide</span></h1>
                    <p>Ikoranabuhanga mu buhinzi rifasha abahinzi kubona amakuru yizewe ya RAB vuba na bwangu. (Your trusted agricultural AI assistant.)</p>
                </div>
                <div className="header-image-container">
                    <img src={farmer} alt="Rwandan Farmer using tech" />
                </div>
            </div>
        </section>
    );
}

export default DashboardHeader;