import styles from './Message.module.scss'
export const showMessage = (message: string) => {
    const messageBox = document.createElement("div");
    messageBox.textContent = message;

    messageBox.classList.add(styles.messageBox);

    messageBox.style.display = "none";

    document.body.appendChild(messageBox);

    messageBox.style.display = "block";

    setTimeout(() => {
        messageBox.style.display = "none";
        document.body.removeChild(messageBox);
    }, 3000);
};
