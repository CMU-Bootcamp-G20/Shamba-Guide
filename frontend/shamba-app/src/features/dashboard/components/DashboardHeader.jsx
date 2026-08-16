import farmer from '../../../assets/farmer.png'


function DashboardHeader() {
    return (
        <section className="welcome-banner">
        <div className="header-div">
            <div>
                <img src={farmer} alt="a farmer making communication"/>
            </div>
            <div>
                <h1 style={{ lineHeight: "1.6rem"}}>
                    Welcome to Shamba Guide 
                </h1>
                </div>
            </div>
            {/* <div className="welcome-date">
                Today
            </div> */}
        </section>
    );
}

export default DashboardHeader;