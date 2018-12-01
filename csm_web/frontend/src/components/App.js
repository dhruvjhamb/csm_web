import React from "react";
import { MemoryRouter as Router, Route, Link } from "react-router-dom";
import ReactDOM from "react-dom";
import Section from "./Section";
import Navbar from "./Navbar";

class App extends React.Component {
  state = {
    sections: {},
    profiles: {}
  };

  componentDidMount() {
    const profilesEndpoint = "/scheduler/profiles/";
    fetch(profilesEndpoint)
      .then(response => response.json())
      .then(data => {
        const profileIDs = data.profiles;
        for (let id of profileIDs) {
          fetch(`${profilesEndpoint}${id}/`)
            .then(response => response.json())
            .then(profileData =>
              this.setState((state, props) => {
                return {
                  profiles: { [id]: profileData, ...state.profiles },
                  sections: { ...profileData.sections, ...state.sections }
                };
              })
            );
        }
      });
  }

  render() {
    return (
      <div>
        <Router>
          <div>
            <Navbar sections={this.state.sections} />
            <Route
              path="/sections/:id"
              render={({ match }) => (
                <Section {...this.state.sections[match.params.id]} />
              )}
            />
          </div>
        </Router>
      </div>
    );
  }
}

const wrapper = document.getElementById("app");

wrapper ? ReactDOM.render(<App />, wrapper) : null;
export default App;
