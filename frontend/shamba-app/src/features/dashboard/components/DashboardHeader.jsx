function    DashboardHeader() {
    return (
        <section className="welcome-banner">
            <div>
                <p className="welcome-label">AGRICULTURAL INSIGHTS</p>

                <h1>
                    Welcome to Shamba Guide 
                </h1>

                <p>
                    Here's an overview of conversations and agricultural
                    questions from your assistant.
                </p>
            </div>

            <div className="welcome-date">
                Today
            </div>
        </section>
    );
}

export default DashboardHeader;