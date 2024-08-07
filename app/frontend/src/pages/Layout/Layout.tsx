import { Link, NavLink, Outlet } from "react-router-dom";

import styles from "./Layout.module.css";

import searchLogo from "../../assets/search.svg";

export const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link to="/" className={styles.headerTitleContainer}>
                        <img src={searchLogo} alt="Azure Cognitive Search logo" className={styles.headerLogo} />
                        <h3 className={styles.headerTitle}>Search Comparision Tool</h3>
                    </Link>
                    <nav>
                        <ul className={styles.headerNavList}>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Text
                                </NavLink>
                            </li>
                        </ul>
                    </nav>
                </div>
            </header>
            <div className={styles.content}>
                <Outlet />
            </div>
        </div>
    );
};
