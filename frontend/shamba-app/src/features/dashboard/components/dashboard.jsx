import Card from "./Card"
function Dashboard(){
    return (
        <>
        <div className="dashboard">
            <h1>
                Dashboard
            </h1>
            <div className="card-grid">
            <Card/>
            <Card/>
            </div>
        </div>
        </>
    )
}

export default Dashboard