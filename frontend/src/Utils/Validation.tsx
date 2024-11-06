/**
 * @description a utility function to validate password
 */


export const checkPasswordComplexity = (password: string) => {
    const lengthRule = /.{8,}/; // at least 8 characters
    const numberRule = /.*[0-9].*/; // includes a number
    const lowerCaseRule = /.*[a-z].*/; // includes a lowercase letter
    const upperCaseRule = /.*[A-Z].*/; // includes an uppercase letter

    return lengthRule.test(password) &&
        numberRule.test(password) &&
        lowerCaseRule.test(password) &&
        upperCaseRule.test(password);
};

/**
 * @description a utility function to validate email
 */

export const checkEmail = (email: string) => {
    const atRule = /^[^@]*@[^@]*$/; // check availability just 1 @ symbol
    const lengthRule = /.{8,}/; // at least 8 characters
    const lengthNameRule = /.{3,}@.{3,}/; // name should has at least 3 symbols
    const extensionRule = /^[^@]*@[^@]*[a-zA-Z]+\.[a-zA-Z]+$/; // check extension

    return atRule.test(email) &&
        lengthRule.test(email) &&
        lengthNameRule.test(email) &&
        extensionRule.test(email);
}
